"""
backend/test_planner_loop_hardening.py

Stand-in Test Suite for Planner and Agent Loop Hardening Mechanics.

Tests:
1. Fenced JSON Parsing (Markdown code blocks)
2. JSON Extraction from Surrounding Prose
3. One Repair Attempt Success (Mocked GeminiPlanner)
4. Repair Attempt Failure (Mocked GeminiPlanner)
5. Repeated Identical Call Detection (Stuck Loop -> 'stuck_loop')
6. Total LLM Call Budget Cap (Budget Exhaustion -> 'budget_exhausted')
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Ensure backend root is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# UTF-8 encoding for Windows terminal output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.agent.planner import GeminiPlanner, ScriptedPlanner, parse_and_validate_decision
from app.agent.loop import run_agent


def test_fenced_json():
    """STAND-IN TEST 1: Parses JSON wrapped in markdown code fences."""
    fenced_raw = """```json
{
  "action": "finish",
  "tool": "",
  "args": {},
  "reason": "Goal satisfied",
  "final_answer": "Successfully parsed fenced JSON"
}
```"""
    decision = parse_and_validate_decision(fenced_raw)
    assert decision["action"] == "finish"
    assert decision["final_answer"] == "Successfully parsed fenced JSON"
    print("  [PASS] Stand-In Test 1: Fenced JSON parsed successfully.")


def test_json_with_trailing_prose():
    """STAND-IN TEST 2: Extracts JSON object when surrounded by prose text."""
    prose_raw = """Here is the decision you requested:
{
  "action": "tool",
  "tool": "get_customer_feedback",
  "args": {},
  "reason": "Fetch customer feedback",
  "final_answer": ""
}
Hope this helps with your analysis!"""
    decision = parse_and_validate_decision(prose_raw)
    assert decision["action"] == "tool"
    assert decision["tool"] == "get_customer_feedback"
    print("  [PASS] Stand-In Test 2: Extracted JSON object from surrounding text.")


def test_repair_success():
    """STAND-IN TEST 3: One repair attempt succeeds after initial bad JSON."""
    bad_json = "This is not JSON text at all."
    repaired_json = '{"action": "finish", "tool": "", "args": {}, "reason": "Repaired JSON", "final_answer": "Repaired OK"}'

    planner = GeminiPlanner()

    # Mock generate_text to fail on 1st call and succeed on 2nd repair call
    with patch("app.agent.planner.generate_text", side_effect=[bad_json, repaired_json]):
        state = {"goal": "Test repair", "history": [], "step_count": 0, "max_steps": 10}
        decision = planner.decide_next_action(state)

    assert decision["action"] == "finish"
    assert decision["final_answer"] == "Repaired OK"
    print("  [PASS] Stand-In Test 3: Repair attempt succeeded on 2nd call.")


def test_repair_failure():
    """STAND-IN TEST 4: Repair attempt fails when 2nd call also produces bad text."""
    bad_json1 = "Not valid JSON 1"
    bad_json2 = "Still not valid JSON 2"

    planner = GeminiPlanner()

    with patch("app.agent.planner.generate_text", side_effect=[bad_json1, bad_json2]):
        state = {"goal": "Test repair fail", "history": [], "step_count": 0, "max_steps": 10}
        decision = planner.decide_next_action(state)

    assert decision["action"] == "invalid"
    assert "Failed to parse LLM planner JSON" in decision["reason"]
    print("  [PASS] Stand-In Test 4: Repair failure returned invalid decision gracefully.")


def test_stuck_loop_detection():
    """STAND-IN TEST 5: Detects 3 identical tool calls with same args and halts with 'stuck_loop'."""
    # 3 identical tool decisions
    repeated_decisions = [
        {"action": "tool", "tool": "get_customer_feedback", "args": {}, "reason": "Call 1"},
        {"action": "tool", "tool": "get_customer_feedback", "args": {}, "reason": "Call 2"},
        {"action": "tool", "tool": "get_customer_feedback", "args": {}, "reason": "Call 3"},
    ]

    planner = ScriptedPlanner(repeated_decisions)
    res = run_agent(
        goal="Test stuck loop",
        planner=planner,
        max_steps=10,
        llm_budget=12
    )

    assert res["status"] == "stuck_loop"
    assert "stuck loop" in res["final_answer"].lower()
    print("  [PASS] Stand-In Test 5: Stuck loop detected after 3 identical tool calls.")


def test_budget_exhaustion():
    """STAND-IN TEST 6: Halts execution with 'budget_exhausted' when llm_budget is exceeded."""
    many_decisions = [
        {"action": "tool", "tool": "get_customer_feedback", "args": {}, "reason": "Call 1"},
        {"action": "tool", "tool": "search_memory", "args": {"query": "checkout"}, "reason": "Call 2"},
        {"action": "tool", "tool": "search_memory", "args": {"query": "login"}, "reason": "Call 3"},
    ]

    planner = ScriptedPlanner(many_decisions)
    # Set tight budget of 2 calls
    res = run_agent(
        goal="Test budget limit",
        planner=planner,
        max_steps=10,
        llm_budget=2
    )

    assert res["status"] == "budget_exhausted"
    assert res["llm_calls"] == 2
    assert "budget" in res["final_answer"].lower()
    print("  [PASS] Stand-In Test 6: LLM budget exhaustion halted execution.")


def run_all_stand_in_tests():
    print("=" * 80)
    print(" EchoInsight Agent Planner & Loop Hardening Stand-In Test Suite")
    print("=" * 80)

    test_fenced_json()
    test_json_with_trailing_prose()
    test_repair_success()
    test_repair_failure()
    test_stuck_loop_detection()
    test_budget_exhaustion()

    print("\n" + "=" * 80)
    print(" ALL STAND-IN HARDENING TESTS PASSED SUCCESSFULLY (6/6)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all_stand_in_tests()
