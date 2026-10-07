"""
backend/app/agent/planner.py

Planner layer for the EchoInsight autonomous agent.
Provides a swappable Planner interface, a ScriptedPlanner for deterministic testing,
and a GeminiPlanner for LLM-driven decision making.
"""

from abc import ABC, abstractmethod
import json
from typing import Any, Dict, List, Optional
from .tools import TOOL_REGISTRY
from ..services.llm_client import generate_text


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
            "action": "tool" | "finish",
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
    Constructs a concise prompt containing available tools, task goal, and step history,
    then parses and validates the model's JSON decision.
    """

    def decide_next_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        goal = state.get("goal", "")
        history = state.get("history", [])

        # Format tool descriptions from TOOL_REGISTRY
        tool_descriptions = []
        for name, meta in TOOL_REGISTRY.items():
            args_desc = ", ".join([f"{k}: {v}" for k, v in meta.get("args", {}).items()])
            approval_str = " (Requires Approval)" if meta.get("requires_approval") else ""
            tool_descriptions.append(f"- {name}({args_desc}): {meta.get('description')}{approval_str}")
        tools_str = "\n".join(tool_descriptions)

        # Format concise history string for the LLM
        history_lines = []
        for item in history:
            role = item.get("role", "system")
            content = item.get("content", "")
            history_lines.append(f"[{role}]: {content}")
        history_str = "\n".join(history_lines) if history_lines else "None"

        prompt = f"""
You are an autonomous AI Product Manager Agent for EchoInsight.
Goal: {goal}

Available Tools:
{tools_str}

Execution History:
{history_str}

Instructions:
1. Select ONE tool to call OR choose action "finish" if goal is satisfied.
2. Return ONLY raw valid JSON matching this exact schema:
{{
  "action": "tool" or "finish",
  "tool": "tool_name_here",
  "args": {{"arg_name": "arg_value"}},
  "reason": "Short explanation of why this step was chosen",
  "final_answer": "Summary response if action is finish, else empty string"
}}
"""

        try:
            raw_response = generate_text(prompt, json_mode=True)

            # Clean markdown code block formatting if present
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

            decision = json.loads(cleaned)

            # Validate decision dictionary structure
            if not isinstance(decision, dict):
                raise ValueError("Planner response is not a valid JSON object.")

            action = decision.get("action", "tool")
            tool_name = decision.get("tool", "")
            args = decision.get("args", {})
            reason = decision.get("reason", "")
            final_answer = decision.get("final_answer", "")

            return {
                "action": action,
                "tool": str(tool_name),
                "args": args if isinstance(args, dict) else {},
                "reason": str(reason),
                "final_answer": str(final_answer)
            }

        except Exception as e:
            # Return fallback invalid decision envelope to be handled safely by the agent loop
            return {
                "action": "invalid",
                "tool": "",
                "args": {},
                "reason": f"Failed to parse LLM planner JSON: {str(e)}",
                "final_answer": ""
            }
