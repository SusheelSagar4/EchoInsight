"""
backend/app/agent/planner.py

Planner layer for the EchoInsight autonomous agent.
Provides a swappable Planner interface, a ScriptedPlanner for deterministic testing,
and a GeminiPlanner for LLM-driven decision making with JSON robustness, repair attempts,
prompt hygiene, and LLM API error classification.
"""

from abc import ABC, abstractmethod
import json
import re
from typing import Any, Dict, List, Optional
from .tools import classify_error, TOOL_REGISTRY
from ..services.llm_client import generate_text


def extract_json_from_text(text: str) -> str:
    """
    Strips markdown code fences (```json ... ```) and extracts the first JSON object
    from text if there is leading or trailing prose.
    """
    if not text or not isinstance(text, str):
        return ""

    cleaned = text.strip()

    # 1. Strip markdown code fences if present
    if "```" in cleaned:
        fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
        if fence_match:
            cleaned = fence_match.group(1).strip()
        else:
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

    # 2. Extract first JSON object {...} if surrounded by non-JSON prose
    if not (cleaned.startswith("{") and cleaned.endswith("}")):
        json_obj_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_obj_match:
            cleaned = json_obj_match.group(1).strip()

    return cleaned


def parse_and_validate_decision(raw_text: str) -> Dict[str, Any]:
    """
    Extracts, parses, and schema-validates a decision JSON string against TOOL_REGISTRY.
    Raises ValueError if parsing or validation fails.
    """
    extracted = extract_json_from_text(raw_text)
    if not extracted:
        raise ValueError("No JSON object found in response text.")

    try:
        decision = json.loads(extracted)
    except Exception as parse_err:
        raise ValueError(f"JSON syntax error: {str(parse_err)}")

    if not isinstance(decision, dict):
        raise ValueError("Decision output is not a JSON object dictionary.")

    action = decision.get("action")
    if action not in ["tool", "finish", "invalid"]:
        raise ValueError(f"Invalid 'action' field: '{action}'. Must be 'tool' or 'finish'.")

    if action == "tool":
        tool_name = decision.get("tool", "")
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError("Action 'tool' requires a non-empty string 'tool' field.")

        if tool_name not in TOOL_REGISTRY:
            raise ValueError(
                f"Tool '{tool_name}' is not registered in TOOL_REGISTRY. Valid tools: {list(TOOL_REGISTRY.keys())}"
            )

        args = decision.get("args")
        if args is not None and not isinstance(args, dict):
            raise ValueError("Tool 'args' field must be a dictionary.")

    reason = decision.get("reason", "")
    final_answer = decision.get("final_answer", "")

    return {
        "action": action,
        "tool": str(decision.get("tool", "")),
        "args": decision.get("args", {}) if isinstance(decision.get("args"), dict) else {},
        "reason": str(reason),
        "final_answer": str(final_answer)
    }


class Planner(ABC):
    """
    Abstract base class for agent planners.
    A Planner receives the current execution state (goal, history, observations)
    and decides the next action.
    """

    @abstractmethod
    def decide_next_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given the current state dictionary, returns a decision dictionary matching:
        {
            "action": "tool" | "finish" | "invalid" | "api_error",
            "tool": str,
            "args": dict,
            "reason": str,
            "final_answer": str
        }
        """
        pass


class ScriptedPlanner(Planner):
    """
    Stand-in deterministic planner for isolated unit testing of agent loop mechanics.
    Replays a predefined sequence of decision dictionaries in order.
    """

    def __init__(self, decisions: List[Dict[str, Any]]):
        self.decisions = list(decisions)
        self.step_index = 0

    def decide_next_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if self.step_index < len(self.decisions):
            decision = dict(self.decisions[self.step_index])
            self.step_index += 1
            args = dict(decision.get("args", {}))
            if args.get("item_id") == "$LAST_CREATED_ID":
                args["item_id"] = state.get("last_created_id", "ENG-101")
            decision["args"] = args
            return decision

        # Fallback decision if script runs out of pre-scripted decisions
        return {
            "action": "finish",
            "tool": "",
            "args": {},
            "reason": "Scripted decision list exhausted.",
            "final_answer": "Finished replaying scripted planner decisions."
        }


class GeminiPlanner(Planner):
    """
    LLM-driven Planner powered by Google Gemini API via llm_client.generate_text.
    Includes Markdown fence stripping, regex extraction, 1-attempt JSON repair on malformed text,
    LLM API error classification via classify_error, and prompt history summarization.
    """

    def decide_next_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        goal = state.get("goal", "")
        history = state.get("history", [])
        step_count = state.get("step_count", 0)
        max_steps = state.get("max_steps", 10)
        logger = state.get("planner_logger")

        # Format tool descriptions from TOOL_REGISTRY
        tool_descriptions = []
        for name, meta in TOOL_REGISTRY.items():
            args_desc = ", ".join([f"{k}: {v}" for k, v in meta.get("args", {}).items()])
            approval_str = " (Requires Approval)" if meta.get("requires_approval") else ""
            tool_descriptions.append(f"- {name}({args_desc}): {meta.get('description')}{approval_str}")
        tools_str = "\n".join(tool_descriptions)

        # Prompt Hygiene: Summarize history (keep last 3 in full, one short line for older)
        history_lines = []
        num_items = len(history)
        full_start_idx = max(0, num_items - 3)

        for i, item in enumerate(history):
            role = item.get("role", "system")
            content = item.get("content", "")

            if i < full_start_idx:
                short_content = content.replace("\n", " ")
                if len(short_content) > 100:
                    short_content = short_content[:100] + "..."
                history_lines.append(f"[{role}] (Step {i+1}): {short_content}")
            else:
                history_lines.append(f"[{role}] (Step {i+1}): {content}")

        history_str = "\n".join(history_lines) if history_lines else "None"

        prompt = f"""
You are an autonomous AI Product Manager Agent for EchoInsight.
Goal: {goal}
Current Progress: Step {step_count + 1} of {max_steps}

Available Tools:
{tools_str}

Execution History:
{history_str}

Instructions & Rules:
1. Goal Types & Tool Sequence:
   a) Full PRD & Backlog Pipeline ("Find most important recurring issue, create a PRD, add to backlog"):
      get_customer_feedback -> cluster_feedback_tool -> rank_clusters -> generate_prd_tool -> create_backlog_item -> verify_backlog_item -> finish.
      CRITICAL RULE: Never call a write tool (create_backlog_item) before rank_clusters and generate_prd_tool have succeeded!
   b) Targeted Topic Backlog Item ("Find top recurring complaint about <topic> and create backlog item"):
      search_memory or get_customer_feedback -> create_backlog_item -> verify_backlog_item -> finish.
   c) Read-Only Analytical Query ("Which problem is getting worse?", trend queries, evidence questions):
      Use read-only tools like get_feedback_trend, get_customer_feedback, or search_memory. Do NOT call write tools. Select action "finish" once evidence is gathered.
2. CRITICAL RULE: Always call verify_backlog_item(item_id) immediately after create_backlog_item creates a ticket.
3. CRITICAL RULE: Finish ONLY with evidence gathered from previous tool results.
4. CRITICAL RULE: If no tool exists for the goal or a tool fails repeatedly, finish with a clear status explanation instead of inventing non-existent tools.
5. Select ONE tool to call OR choose action "finish" if the goal is satisfied.
6. Return ONLY raw valid JSON matching this exact schema:
{{
  "action": "tool" or "finish",
  "tool": "tool_name_here",
  "args": {{"arg_name": "arg_value"}},
  "reason": "Short explanation of why this step was chosen",
  "final_answer": "Detailed summary response with evidence if action is finish, else empty string"
}}
"""
        prompt_len = len(prompt)

        # ---------------------------------------------------------------------
        # 1st Attempt to generate decision from LLM API
        # ---------------------------------------------------------------------
        try:
            raw_response = generate_text(prompt, json_mode=True)
        except Exception as first_api_err:
            err_text = str(first_api_err)
            if logger and callable(logger):
                logger(prompt_len=prompt_len, raw_response="", parse_error=err_text, is_repair=False)

            info = classify_error(err_text)
            return {
                "action": "api_error",
                "tool": "",
                "args": {},
                "error_text": err_text,
                "error_type": info.get("error_type", "other"),
                "retryable": info.get("retryable", False),
                "retry_after_seconds": info.get("retry_after_seconds"),
                "reason": f"LLM API Call Exception: {err_text}",
                "final_answer": ""
            }

        # Validate 1st Attempt raw response
        try:
            decision = parse_and_validate_decision(raw_response)
            if logger and callable(logger):
                logger(prompt_len=prompt_len, raw_response=raw_response[:2000], parse_error=None, is_repair=False)
            return decision
        except ValueError as val_err:
            first_val_error = str(val_err)
            if logger and callable(logger):
                logger(prompt_len=prompt_len, raw_response=raw_response[:2000], parse_error=first_val_error, is_repair=False)

        # ---------------------------------------------------------------------
        # ONE Repair Attempt for genuinely malformed JSON output
        # ---------------------------------------------------------------------
        repair_prompt = f"""
Your previous JSON decision response failed validation with the following error:
{first_val_error}

Please correct your output. Return ONLY a valid JSON object matching the schema with no extra text or markdown formatting:
{{
  "action": "tool" or "finish",
  "tool": "tool_name_here",
  "args": {{}},
  "reason": "explanation",
  "final_answer": ""
}}
"""
        repair_prompt_len = len(repair_prompt)

        # Increment llm_call_notifier if present in state
        notifier = state.get("llm_call_notifier")
        if notifier and callable(notifier):
            notifier()

        try:
            repair_raw_response = generate_text(repair_prompt, json_mode=True)
        except Exception as repair_api_err:
            err_text = str(repair_api_err)
            if logger and callable(logger):
                logger(prompt_len=repair_prompt_len, raw_response="", parse_error=err_text, is_repair=True)

            info = classify_error(err_text)
            return {
                "action": "api_error",
                "tool": "",
                "args": {},
                "error_text": err_text,
                "error_type": info.get("error_type", "other"),
                "retryable": info.get("retryable", False),
                "retry_after_seconds": info.get("retry_after_seconds"),
                "reason": f"LLM API Repair Call Exception: {err_text}",
                "final_answer": ""
            }

        # Validate repair attempt raw response
        try:
            repair_decision = parse_and_validate_decision(repair_raw_response)
            if logger and callable(logger):
                logger(prompt_len=repair_prompt_len, raw_response=repair_raw_response[:2000], parse_error=None, is_repair=True)
            return repair_decision
        except ValueError as repair_val_err:
            second_val_error = str(repair_val_err)
            if logger and callable(logger):
                logger(prompt_len=repair_prompt_len, raw_response=repair_raw_response[:2000], parse_error=second_val_error, is_repair=True)

            return {
                "action": "invalid",
                "tool": "",
                "args": {},
                "reason": f"Failed to parse LLM planner JSON after repair attempt: {second_val_error}",
                "final_answer": ""
            }
