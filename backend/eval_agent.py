"""
backend/eval_agent.py

Evaluation Harness for EchoInsight Autonomous Agent.

==============================================================================
WHAT IS THIS EVALUATION HARNESS FOR? (FOR BEGINNERS)
==============================================================================
This script evaluates the EchoInsight agent against all sample goals defined in
backend/data/sample_goals.json.

Modes:
1. --scripted (Offline Stand-In Mode):
   Uses ScriptedPlanner and pre-recorded decision files from backend/data/scripted/.
   Requires 0 live LLM API calls. Fast, deterministic, and ideal for CI/CD.

2. --live (Live Gemini LLM Mode):
   Uses GeminiPlanner and calls live Google Gemini API to evaluate real LLM reasoning.

Outputs:
- Formatted evaluation table printed to terminal showing mode, LLM calls, and reasons.
- Complete evaluation results saved to backend/data/eval_results.json.
==============================================================================
"""

import argparse
from datetime import datetime, timezone
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure UTF-8 output encoding for Windows command prompts
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent.loop import run_agent
from app.agent.planner import GeminiPlanner, ScriptedPlanner
from app.agent.tools import TOOL_REGISTRY

# Color constants
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

SAMPLE_GOALS_PATH = BACKEND_DIR / "data" / "sample_goals.json"
SCRIPTED_DIR = BACKEND_DIR / "data" / "scripted"
EVAL_RESULTS_PATH = BACKEND_DIR / "data" / "eval_results.json"

# Expected statuses per goal type
EXPECTED_STATUSES = {
    "goal_1": "completed",
    "goal_2": "completed",
    "goal_3": "completed",
    "goal_4": "completed"
}


# Mocks for offline --scripted evaluation to avoid live LLM calls during offline tests
def mock_cluster_feedback_tool(feedback_lines):
    return {
        "ok": True,
        "data": [
            {
                "theme_name": "Checkout Payment Failures",
                "rice_score": 450.0,
                "reach": 150,
                "impact": 3.0,
                "confidence": 1.0,
                "effort": 1.0
            }
        ]
    }


def mock_generate_prd_tool(cluster):
    return {
        "ok": True,
        "data": {
            "title": "PRD: Checkout Payment Failures",
            "problem_statement": "Fix payment gateway timeouts",
            "user_stories": ["As a user, I want reliable payment processing."],
            "acceptance_criteria": ["0 503 errors on checkout."],
            "kpis": ["Payment conversion rate > 98%"]
        }
    }


def run_evaluation(mode: str) -> bool:
    is_live = (mode == "live")
    mode_label = "LIVE GEMINI LLM EVALUATION" if is_live else "SCRIPTED STAND-IN EVALUATION"

    print("=" * 115)
    print(f" {BOLD}EchoInsight Autonomous Agent Evaluation Harness{RESET}")
    print(f" {CYAN}MODE: {mode_label}{RESET}")
    print("=" * 115)

    if not SAMPLE_GOALS_PATH.exists():
        print(f"{RED}Error: sample_goals.json not found at {SAMPLE_GOALS_PATH}{RESET}")
        return False

    with open(SAMPLE_GOALS_PATH, mode="r", encoding="utf-8") as f:
        goals_data = json.load(f)

    # Patch tools in offline scripted mode to guarantee zero live LLM API calls
    if not is_live:
        TOOL_REGISTRY["cluster_feedback_tool"]["function"] = mock_cluster_feedback_tool
        TOOL_REGISTRY["generate_prd_tool"]["function"] = mock_generate_prd_tool

    eval_records = []
    all_matched = True
    halt_triggered = False
    halt_reason = ""

    for item in goals_data:
        goal_id = item.get("id")
        goal_text = item.get("goal")
        goal_type = item.get("type")
        expected_status = EXPECTED_STATUSES.get(goal_id, "completed")

        print(f"\nEvaluating Goal [{goal_id}] ({goal_type}): \"{goal_text}\"...")

        # Initialize planner for this goal
        if is_live:
            planner = GeminiPlanner()
        else:
            script_filename = SCRIPTED_FILES_map(goal_id)
            script_path = SCRIPTED_DIR / script_filename
            if not script_path.exists():
                print(f"{RED}  ❌ Scripted file missing: {script_path}{RESET}")
                continue
            with open(script_path, mode="r", encoding="utf-8") as sf:
                decisions = json.load(sf)
            planner = ScriptedPlanner(decisions)

        # Run agent loop (auto-approve write tools during evaluation)
        result = run_agent(
            goal=goal_text,
            planner=planner,
            approval_handler=lambda tool, args, reason: True
        )

        status = result.get("status")
        steps = result.get("steps", 0)
        llm_calls = result.get("llm_calls", 0)
        final_ans = result.get("final_answer", "")
        trace = result.get("trace", [])

        # Count retries
        retries_count = result.get("retries", sum(1 for evt in trace if evt.get("event_type") == "retry"))

        # Check if verification occurred
        verification_happened = any(
            (evt.get("event_type") == "verification" and evt.get("passed")) or
            (evt.get("event_type") == "tool_result" and evt.get("tool") == "verify_backlog_item" and evt.get("result", {}).get("ok"))
            for evt in trace
        )

        status_matched = (status == expected_status)
        if not status_matched:
            all_matched = False

        record = {
            "goal_id": goal_id,
            "goal_type": goal_type,
            "goal": goal_text,
            "status": status,
            "expected_status": expected_status,
            "status_matched": status_matched,
            "steps_used": steps,
            "llm_calls": llm_calls,
            "retries": retries_count,
            "verification_happened": verification_happened,
            "reason": final_ans,
            "final_answer": final_ans
        }
        eval_records.append(record)

        match_str = f"{GREEN}MATCH{RESET}" if status_matched else f"{RED}MISMATCH{RESET}"
        print(f"  --> Status: {status} (Expected: {expected_status}) [{match_str}]")
        print(f"      Reason / Final Answer: {final_ans}")
        print(f"      Steps: {steps} | LLM Calls: {llm_calls} | Retries: {retries_count} | Verified: {verification_happened}")

        # Stop evaluation immediately if halted due to quota or LLM error
        if status in ["halted_quota", "halted_llm_error"]:
            halt_triggered = True
            halt_reason = f"Evaluation halted immediately on goal [{goal_id}] due to '{status}': {final_ans}"
            print(f"\n{RED}🛑 [EVALUATION HALTED] {halt_reason}{RESET}\n")
            all_matched = False
            break

    # Output Evaluation Summary Table
    print("\n" + "=" * 125)
    print(f" {BOLD}EVALUATION RESULTS SUMMARY ({mode_label}){RESET}")
    print("=" * 125)
    print(f"{'Goal ID':<9} | {'Type':<15} | {'Status':<20} | {'Expected':<12} | {'Match':<6} | {'Steps':<5} | {'LLM Calls':<9} | {'Reason / Summary':<38}")
    print("-" * 125)

    for r in eval_records:
        match_symbol = f"{GREEN}YES{RESET}" if r["status_matched"] else f"{RED}NO{RESET}"
        reason_trunc = r['reason'].replace('\n', ' ')
        if len(reason_trunc) > 38:
            reason_trunc = reason_trunc[:35] + "..."
        print(f"{r['goal_id']:<9} | {r['goal_type']:<15} | {r['status']:<20} | {r['expected_status']:<12} | {match_symbol:<15} | {r['steps_used']:<5} | {r['llm_calls']:<9} | {reason_trunc:<38}")

    print("=" * 125)

    if halt_triggered:
        print(f"{RED}⚠️ HALT WARNING: {halt_reason}{RESET}\n")

    # Save evaluation report to backend/data/eval_results.json
    eval_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "mode_label": mode_label,
        "overall_matched": all_matched,
        "halt_triggered": halt_triggered,
        "halt_reason": halt_reason if halt_triggered else None,
        "results": eval_records
    }

    try:
        EVAL_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(EVAL_RESULTS_PATH, mode="w", encoding="utf-8") as ef:
            json.dump(eval_payload, ef, indent=2)
        print(f"💾 Saved evaluation report to: {EVAL_RESULTS_PATH}\n")
    except Exception as e:
        print(f"{RED}Warning: Failed to save eval_results.json: {str(e)}{RESET}\n")

    return all_matched


def SCRIPTED_FILES_map(goal_id: str) -> str:
    mapping = {
        "goal_1": "goal_1_prd_backlog.json",
        "goal_2": "goal_2_topic_backlog.json",
        "goal_3": "goal_3_read_only_trend.json",
        "goal_4": "goal_4_impossible.json"
    }
    return mapping.get(goal_id, f"{goal_id}.json")


def main():
    parser = argparse.ArgumentParser(description="EchoInsight Autonomous Agent Evaluation Harness")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--scripted", action="store_true", help="Run offline stand-in evaluation using ScriptedPlanner (default)")
    group.add_argument("--live", action="store_true", help="Run live LLM evaluation using GeminiPlanner")

    args = parser.parse_args()
    mode = "live" if args.live else "scripted"

    success = run_evaluation(mode)
    if not success and mode == "scripted":
        sys.exit(1)


if __name__ == "__main__":
    main()
