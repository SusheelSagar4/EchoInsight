"""
backend/app/agent/cli.py

CLI runner for the EchoInsight autonomous agent.

==============================================================================
WHAT IS THIS CLI FOR? (FOR BEGINNERS)
==============================================================================
This CLI allows developers and PMs to run the EchoInsight AI agent directly from
the terminal command line.

Usage:
  # Live Gemini LLM Mode:
  python -m app.agent.cli "Process customer feedback and create backlog tickets"

  # Offline Scripted Mode (for demos and tests):
  python -m app.agent.cli "Offline task goal" --scripted backend/data/sample_decisions.json

Features:
- Prints real-time trace events live with formatted timestamps as the agent works.
- Interactive CLI approvals: Prompts (y/n) when write tools require human confirmation.
==============================================================================
"""

import argparse
from datetime import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend root to Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure UTF-8 output encoding for Windows command prompts
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.agent.loop import run_agent
from app.agent.planner import GeminiPlanner, ScriptedPlanner


def format_timestamp(iso_str: Optional[str] = None) -> str:
    """Format UTC ISO timestamp to friendly local time string."""
    try:
        if iso_str:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        else:
            dt = datetime.now()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def live_event_printer(event: Dict[str, Any]) -> None:
    """Callback function that prints agent trace events live to stdout as they occur."""
    ts = format_timestamp(event.get("timestamp"))
    event_type = str(event.get("event_type", "event")).upper()
    step = event.get("step")
    step_prefix = f"[Step {step}] " if step else ""

    if event_type == "GOAL_RECEIVED":
        print(f"\n[{ts}] 🎯 [GOAL RECEIVED] Goal: \"{event.get('goal')}\"")

    elif event_type == "DECISION":
        dec = event.get("decision", {})
        action = dec.get("action", "")
        tool = dec.get("tool", "")
        reason = dec.get("reason", "")
        print(f"[{ts}] 🧠 {step_prefix}[DECISION] Action: '{action}' | Tool: '{tool}' | Reason: \"{reason}\"")

    elif event_type == "TOOL_CALL":
        tool = event.get("tool", "")
        attempt = event.get("attempt", 1)
        attempt_str = f" (Attempt #{attempt})" if attempt > 1 else ""
        print(f"[{ts}] ⚙️  {step_prefix}[TOOL CALL] Executing tool '{tool}'{attempt_str}...")

    elif event_type == "TOOL_RESULT":
        tool = event.get("tool", "")
        result = event.get("result", {})
        ok = result.get("ok", False)
        status_symbol = "✅ Success" if ok else f"❌ Failed ({result.get('error_type', 'error')})"
        print(f"[{ts}] 📊 {step_prefix}[TOOL RESULT] {tool}: {status_symbol}")

    elif event_type == "RETRY":
        tool = event.get("tool", "")
        attempt = event.get("attempt", 1)
        wait_sec = event.get("wait_seconds", 30)
        print(f"[{ts}] ⏳ {step_prefix}[RETRY] Tool '{tool}' transient error. Retrying attempt #{attempt + 1} in {wait_sec}s...")

    elif event_type == "APPROVAL_REQUESTED":
        print(f"[{ts}] ⚠️  {step_prefix}[APPROVAL REQUESTED] Tool '{event.get('tool')}' requires human confirmation.")

    elif event_type == "APPROVAL_RESULT":
        approved = event.get("approved", False)
        result_str = "APPROVED ✅" if approved else "REJECTED ❌"
        print(f"[{ts}] 🛡️  {step_prefix}[APPROVAL RESULT] Human decision: {result_str}")

    elif event_type == "VERIFICATION":
        passed = event.get("passed", False)
        if passed:
            print(f"[{ts}] 🔍 {step_prefix}[VERIFICATION] Item '{event.get('item_id')}' verified successfully.")
        else:
            unverified = event.get("unverified_items", [])
            print(f"[{ts}] ✋ {step_prefix}[VERIFICATION REFUSAL] Cannot finish yet! Unverified items: {unverified}")

    elif event_type == "FINISH":
        final_ans = event.get("final_answer", "")
        print(f"[{ts}] 🎉 {step_prefix}[FINISH] Task Completed! Final Answer: {final_ans}")

    elif event_type == "HALTED":
        reason = event.get("reason", "")
        print(f"[{ts}] 🛑 [HALTED] Run halted. Reason: {reason}")


def cli_approval_handler(tool_name: str, args: Dict[str, Any], reason: str) -> bool:
    """
    Interactive CLI human approval handler.
    Prints tool name, arguments, and reason, then prompts for y/n confirmation.
    """
    print("\n" + "=" * 65)
    print(f" ⚠️  HUMAN APPROVAL REQUIRED FOR WRITE TOOL: '{tool_name}'")
    print("=" * 65)
    print(f"  - Action Reason: {reason}")
    print(f"  - Arguments: {json.dumps(args, indent=4)}")
    print("-" * 65)

    while True:
        try:
            choice = input("  Approve execution of this action? (y/n): ").strip().lower()
            if choice in ["y", "yes"]:
                print("  --> User selected: YES (Action Approved)\n")
                return True
            elif choice in ["n", "no"]:
                print("  --> User selected: NO (Action Rejected)\n")
                return False
            else:
                print("  Please enter 'y' or 'n'.")
        except (KeyboardInterrupt, EOFError):
            print("\n  --> Execution interrupted. Defaulting to REJECTED.\n")
            return False


def main():
    parser = argparse.ArgumentParser(description="EchoInsight Autonomous Agent CLI Runner")
    parser.add_argument("goal", nargs="?", default="Analyze customer feedback and create prioritized backlog items", help="The natural language goal for the agent")
    parser.add_argument("--live", action="store_true", help="Explicitly run live Gemini LLM reasoning mode (default)")
    parser.add_argument("--scripted", type=str, default=None, help="Path to JSON file containing scripted decision list for offline execution")
    parser.add_argument("--max-steps", type=int, default=10, help="Maximum execution steps allowed (default: 10)")

    parsed_args = parser.parse_args()

    goal_text = parsed_args.goal.strip()
    scripted_path_str = parsed_args.scripted
    max_steps = parsed_args.max_steps

    print("=" * 70)
    print(" ⚡ EchoInsight Autonomous Agent CLI Engine")
    print("=" * 70)

    # Initialize swappable planner based on CLI flags
    if scripted_path_str:
        scripted_path = Path(scripted_path_str)
        if not scripted_path.exists():
            print(f"❌ Error: Scripted decision file not found at {scripted_path}")
            sys.exit(1)
        try:
            with open(scripted_path, mode="r", encoding="utf-8") as f:
                decisions = json.load(f)
            planner = ScriptedPlanner(decisions)
            print(f"🤖 Planner Mode: ScriptedPlanner ({len(decisions)} decisions loaded from {scripted_path.name})")
        except Exception as e:
            print(f"❌ Error loading scripted JSON decisions: {str(e)}")
            sys.exit(1)
    else:
        planner = GeminiPlanner()
        print("🤖 Planner Mode: GeminiPlanner (Live LLM reasoning via Gemini API)")

    print(f"🎯 Target Goal: \"{goal_text}\"")
    print(f"🔢 Step Cap: {max_steps} steps")
    print("-" * 70)

    # Execute agent run
    result = run_agent(
        goal=goal_text,
        planner=planner,
        approval_handler=cli_approval_handler,
        max_steps=max_steps,
        event_callback=live_event_printer
    )

    print("\n" + "=" * 70)
    print(f" 🏁 RUN EXECUTION COMPLETE")
    print(f"    - Run ID: {result.get('run_id')}")
    print(f"    - Final Status: {result.get('status')}")
    print(f"    - Total Steps: {result.get('steps')}")
    print(f"    - Final Answer: {result.get('final_answer')}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
