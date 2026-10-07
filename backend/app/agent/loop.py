"""
backend/app/agent/loop.py

Core Agent Loop for EchoInsight.

==============================================================================
WHAT IS THE AGENT LOOP? (FOR BEGINNERS)
==============================================================================
An AI agent works in a cyclic loop:
1. PERCEIVE: Observe current state & user goal.
2. DECIDE: Ask Planner what tool to run next.
3. VALIDATE & APPROVE: Check tool registry & request human approval if required.
4. EXECUTE: Call tool, handling retries for temporary rate limits/timeouts.
5. RECORD & PERSIST: Log trace events and update execution history.
6. REPEAT until task is complete or step cap is reached.
==============================================================================
"""

from datetime import datetime, timezone
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

from .planner import Planner
from .tools import TOOL_REGISTRY

# Resolve backend directory and run persistence path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"


def truncate_text_for_history(text: str, max_len: int = 400) -> str:
    """
    Truncates large tool output text for the planner's prompt history,
    while full raw results remain preserved in the event trace.
    """
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"... [truncated {len(text) - max_len} chars]"


def save_run(run_id: str, run_payload: Dict[str, Any]) -> None:
    """
    Saves run execution record and event trace to backend/data/runs/<run_id>.json.
    """
    try:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = RUNS_DIR / f"{run_id}.json"
        with open(file_path, mode="w", encoding="utf-8") as f:
            json.dump(run_payload, f, indent=2)
    except Exception as e:
        print(f"[Run Persistence Warning] Failed to save run {run_id}: {str(e)}")


def run_agent(
    goal: str,
    planner: Planner,
    approval_handler: Optional[Callable[[str, Dict[str, Any], str], bool]] = None,
    max_steps: int = 10,
    sleep_fn: Callable[[float], None] = time.sleep
) -> Dict[str, Any]:
    """
    Runs the main agent loop.

    Args:
        goal (str): The natural language objective for the agent.
        planner (Planner): The planner engine instance (ScriptedPlanner or GeminiPlanner).
        approval_handler (Callable): Optional function to request human approval for write tools.
        max_steps (int): Maximum number of execution steps before halting.
        sleep_fn (Callable): Function used for sleeping during retries (overridden in tests).

    Returns:
        Dict: {
            "run_id": str,
            "status": "completed" | "halted_quota" | "rejected_by_human" |
                      "max_steps_reached" | "invalid_planner_output" | "failed",
            "final_answer": str,
            "steps": int,
            "trace": list[dict]
        }
    """
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    trace: List[Dict[str, Any]] = []
    history: List[Dict[str, str]] = []

    # Verification Guard & Safety Tracking
    created_unverified_items: Set[str] = set()
    last_created_id: Optional[str] = None
    human_rejection_occurred: bool = False
    consecutive_invalid: int = 0
    step_count: int = 0

    def record_event(event_type: str, details: Dict[str, Any]) -> None:
        trace.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **details
        })

    # Record initial goal
    record_event("goal_received", {"goal": goal})
    history.append({"role": "user", "content": f"Task Goal: {goal}"})

    while step_count < max_steps:
        state = {
            "goal": goal,
            "history": history,
            "step_count": step_count,
            "last_created_id": last_created_id,
            "created_unverified_items": sorted(list(created_unverified_items))
        }


        # Step 1: Ask Planner for next action decision
        decision = planner.decide_next_action(state)
        action = decision.get("action", "")
        tool_name = decision.get("tool", "")
        args = decision.get("args", {})
        reason = decision.get("reason", "")
        final_answer = decision.get("final_answer", "")

        record_event("decision", {
            "step": step_count + 1,
            "decision": decision
        })

        # Step 2A: Handle "finish" action
        if action == "finish":
            # Verification Guard Enforcement:
            # Check if any created backlog items have not been verified yet
            if created_unverified_items:
                unverified_list = sorted(list(created_unverified_items))
                record_event("verification", {
                    "step": step_count + 1,
                    "unverified_items": unverified_list,
                    "passed": False
                })
                obs_refusal = (
                    f"[Verification Guard Refusal] Cannot finish task yet. The following backlog item(s) "
                    f"were created but not verified with verify_backlog_item: {', '.join(unverified_list)}. "
                    f"You must call verify_backlog_item(item_id) for each created item before finishing."
                )
                history.append({"role": "user", "content": obs_refusal})
                step_count += 1
                continue

            # Verification Guard passed
            status = "rejected_by_human" if human_rejection_occurred else "completed"
            ans = final_answer if final_answer else (reason if reason else "Task finished successfully.")
            record_event("finish", {
                "step": step_count + 1,
                "final_answer": ans,
                "status": status
            })

            result_payload = {
                "run_id": run_id,
                "status": status,
                "final_answer": ans,
                "steps": step_count + 1,
                "trace": trace
            }
            save_run(run_id, result_payload)
            return result_payload

        # Step 2B: Handle "tool" action
        if action == "tool":
            # Validate tool_name against TOOL_REGISTRY
            if not tool_name or tool_name not in TOOL_REGISTRY:
                consecutive_invalid += 1
                if consecutive_invalid >= 2:
                    status = "invalid_planner_output"
                    ans = f"Agent halted: Planner made 2 consecutive invalid decisions (Unknown tool '{tool_name}')."
                    record_event("halted", {"status": status, "reason": ans})
                    result_payload = {
                        "run_id": run_id,
                        "status": status,
                        "final_answer": ans,
                        "steps": step_count + 1,
                        "trace": trace
                    }
                    save_run(run_id, result_payload)
                    return result_payload

                obs_invalid = f"[Invalid Decision Error] Tool '{tool_name}' is not registered. Valid tools: {list(TOOL_REGISTRY.keys())}."
                history.append({"role": "user", "content": obs_invalid})
                step_count += 1
                continue

            # Valid tool decision: reset consecutive_invalid
            consecutive_invalid = 0
            tool_meta = TOOL_REGISTRY[tool_name]

            # Approval Guard Enforcement for tools requiring human approval
            if tool_meta.get("requires_approval"):
                record_event("approval_requested", {
                    "step": step_count + 1,
                    "tool": tool_name,
                    "args": args,
                    "reason": reason
                })

                approved = False
                if approval_handler:
                    try:
                        approved = bool(approval_handler(tool_name, args, reason))
                    except Exception as app_err:
                        approved = False

                record_event("approval_result", {
                    "step": step_count + 1,
                    "tool": tool_name,
                    "approved": approved
                })

                if not approved:
                    human_rejection_occurred = True
                    obs_rejection = (
                        f"[Approval Rejection] Human supervisor REJECTED execution of tool '{tool_name}' "
                        f"with args {json.dumps(args)}. Do NOT retry this exact write action."
                    )
                    history.append({"role": "user", "content": obs_rejection})
                    step_count += 1
                    continue

            # Tool Execution Loop with Retries (up to 2 retries = 3 attempts)
            tool_fn = tool_meta["function"]
            max_retries = 2
            tool_res: Optional[Dict[str, Any]] = None

            for attempt in range(1, max_retries + 2):
                record_event("tool_call", {
                    "step": step_count + 1,
                    "attempt": attempt,
                    "tool": tool_name,
                    "args": args
                })

                try:
                    tool_res = tool_fn(**args)
                except TypeError as type_err:
                    tool_res = {
                        "ok": False,
                        "error": f"Invalid tool arguments: {str(type_err)}",
                        "retryable": False,
                        "error_type": "other",
                        "retry_after_seconds": None
                    }
                except Exception as fn_err:
                    tool_res = {
                        "ok": False,
                        "error": f"Tool execution failed: {str(fn_err)}",
                        "retryable": False,
                        "error_type": "other",
                        "retry_after_seconds": None
                    }

                record_event("tool_result", {
                    "step": step_count + 1,
                    "attempt": attempt,
                    "tool": tool_name,
                    "result": tool_res
                })

                if tool_res.get("ok"):
                    break  # Success

                # Handle failures
                error_type = tool_res.get("error_type")
                if error_type == "quota_exhausted":
                    status = "halted_quota"
                    ans = f"Agent halted due to LLM quota exhaustion: {tool_res.get('error')}"
                    record_event("halted", {"status": status, "reason": ans})
                    result_payload = {
                        "run_id": run_id,
                        "status": status,
                        "final_answer": ans,
                        "steps": step_count + 1,
                        "trace": trace
                    }
                    save_run(run_id, result_payload)
                    return result_payload

                if tool_res.get("retryable") and attempt <= max_retries:
                    raw_wait = tool_res.get("retry_after_seconds") or 30
                    wait_sec = min(raw_wait, 60)
                    record_event("retry", {
                        "step": step_count + 1,
                        "attempt": attempt,
                        "tool": tool_name,
                        "wait_seconds": wait_sec
                    })
                    print(f"  [Agent Loop Retry] Tool '{tool_name}' transient error ({error_type}). Waiting {wait_sec}s before retry #{attempt}...")
                    sleep_fn(wait_sec)
                else:
                    break  # Non-retryable error or retries exhausted

            # Update tracking & history after tool call
            if tool_res and tool_res.get("ok"):
                # Track created write items and verifications
                if tool_name == "create_backlog_item":
                    item_data = tool_res.get("data", {})
                    if isinstance(item_data, dict) and item_data.get("id"):
                        item_id_val = item_data["id"]
                        created_unverified_items.add(item_id_val)
                        last_created_id = item_id_val

                elif tool_name == "verify_backlog_item":
                    item_data = tool_res.get("data", {})
                    if isinstance(item_data, dict) and item_data.get("id"):
                        verified_id = item_data["id"]
                        if verified_id in created_unverified_items:
                            created_unverified_items.remove(verified_id)
                            record_event("verification", {
                                "step": step_count + 1,
                                "item_id": verified_id,
                                "passed": True
                            })

                data_content = tool_res.get("data")
                data_str = json.dumps(data_content) if isinstance(data_content, (dict, list)) else str(data_content)
                truncated_data = truncate_text_for_history(data_str, max_len=400)
                history.append({"role": "user", "content": f"[Tool Result: {tool_name}] Success: {truncated_data}"})
            else:
                err_msg = tool_res.get("error") if tool_res else "Unknown tool error"
                err_type = tool_res.get("error_type") if tool_res else "other"
                history.append({"role": "user", "content": f"[Tool Result: {tool_name}] Error ({err_type}): {err_msg}"})

            step_count += 1
            continue

        # Step 2C: Handle invalid action string
        consecutive_invalid += 1
        if consecutive_invalid >= 2:
            status = "invalid_planner_output"
            ans = f"Agent halted: Planner output 2 consecutive invalid actions ('{action}')."
            record_event("halted", {"status": status, "reason": ans})
            result_payload = {
                "run_id": run_id,
                "status": status,
                "final_answer": ans,
                "steps": step_count + 1,
                "trace": trace
            }
            save_run(run_id, result_payload)
            return result_payload

        obs_action_error = f"[Invalid Decision Error] Unknown action '{action}'. Action must be 'tool' or 'finish'."
        history.append({"role": "user", "content": obs_action_error})
        step_count += 1

    # Step cap reached
    status = "max_steps_reached"
    ans = f"Agent stopped: Exceeded maximum step limit ({max_steps} steps)."
    record_event("halted", {"status": status, "reason": ans})
    result_payload = {
        "run_id": run_id,
        "status": status,
        "final_answer": ans,
        "steps": step_count,
        "trace": trace
    }
    save_run(run_id, result_payload)
    return result_payload
