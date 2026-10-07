"""
backend/test_goals.py

Test Suite for Multiple Agent Goal Types & Graceful Failure Handling.

==============================================================================
WHAT IS THIS TEST FOR? (FOR BEGINNERS)
==============================================================================
This script tests the EchoInsight agent against multiple goal types:
1. Full PRD & Backlog Pipeline
2. Targeted Topic Backlog Item
3. Read-Only Analytical Trend Query (Verifies no write/approval requested)
4. Impossible Goal / Non-Existent Tool (Verifies graceful halting)
==============================================================================
"""

import json
import os
import sys
from pathlib import Path

# Add backend root to Python path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent.loop import run_agent
from app.agent.planner import ScriptedPlanner
from app.agent.tools import get_feedback_trend, TOOL_REGISTRY

# Color constants
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


# Mock functions for offline zero-API testing of AI tools
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


# Patch TOOL_REGISTRY for offline test execution
TOOL_REGISTRY["cluster_feedback_tool"]["function"] = mock_cluster_feedback_tool
TOOL_REGISTRY["generate_prd_tool"]["function"] = mock_generate_prd_tool


def test_get_feedback_trend_tool():
    print(f"\n{CYAN}{BOLD}--- Test 0: get_feedback_trend Tool Envelope & Fallback ---{RESET}")
    # Test tool call on query
    res = get_feedback_trend(theme_query="checkout payment failures", top_k=5)
    print(f"Tool output envelope: {json.dumps(res, indent=2)}")

    if not res.get("ok"):
        print(f"{RED}FAIL: get_feedback_trend returned ok=False{RESET}")
        return False

    data = res.get("data", {})
    if "status" not in data or "trend" not in data:
        print(f"{RED}FAIL: Missing expected trend metadata fields in data{RESET}")
        return False

    print(f"{GREEN}PASS: get_feedback_trend envelope and fallback handling verified.{RESET}")
    return True


def test_goal_1_full_pipeline():
    print(f"\n{CYAN}{BOLD}--- Test 1: Full PRD & Backlog Pipeline ---{RESET}")
    script_path = BACKEND_DIR / "data" / "scripted" / "goal_1_prd_backlog.json"
    with open(script_path, mode="r", encoding="utf-8") as f:
        decisions = json.load(f)

    planner = ScriptedPlanner(decisions)
    res = run_agent(
        goal="Find the most important recurring issue, create a PRD, add it to the backlog",
        planner=planner,
        approval_handler=lambda t, a, r: True
    )

    print(f"Run status: {res.get('status')}")
    if res.get("status") != "completed":
        print(f"{RED}FAIL: Goal 1 expected status 'completed', got '{res.get('status')}'{RESET}")
        return False

    print(f"{GREEN}PASS: Goal 1 (Full PRD & Backlog Pipeline) executed successfully.{RESET}")
    return True


def test_goal_2_topic_backlog():
    print(f"\n{CYAN}{BOLD}--- Test 2: Targeted Topic Backlog Item ---{RESET}")
    script_path = BACKEND_DIR / "data" / "scripted" / "goal_2_topic_backlog.json"
    with open(script_path, mode="r", encoding="utf-8") as f:
        decisions = json.load(f)

    planner = ScriptedPlanner(decisions)
    res = run_agent(
        goal="Find the top recurring complaint about checkout payment failures and create a backlog item",
        planner=planner,
        approval_handler=lambda t, a, r: True
    )

    print(f"Run status: {res.get('status')}")
    if res.get("status") != "completed":
        print(f"{RED}FAIL: Goal 2 expected status 'completed', got '{res.get('status')}'{RESET}")
        return False

    print(f"{GREEN}PASS: Goal 2 (Targeted Topic Backlog Item) executed successfully.{RESET}")
    return True


def test_goal_3_read_only_trend():
    print(f"\n{CYAN}{BOLD}--- Test 3: Read-Only Trend Query (No Write Operations) ---{RESET}")
    script_path = BACKEND_DIR / "data" / "scripted" / "goal_3_read_only_trend.json"
    with open(script_path, mode="r", encoding="utf-8") as f:
        decisions = json.load(f)

    planner = ScriptedPlanner(decisions)
    approval_requested = False

    def track_approval(t, a, r):
        nonlocal approval_requested
        approval_requested = True
        return True

    res = run_agent(
        goal="Which problem is getting worse?",
        planner=planner,
        approval_handler=track_approval
    )

    print(f"Run status: {res.get('status')}")
    if res.get("status") != "completed":
        print(f"{RED}FAIL: Goal 3 expected status 'completed', got '{res.get('status')}'{RESET}")
        return False

    if approval_requested:
        print(f"{RED}FAIL: Read-only goal requested write approval unexpectedly!{RESET}")
        return False

    print(f"{GREEN}PASS: Goal 3 (Read-Only Analytical Trend Query) executed with zero write approvals.{RESET}")
    return True


def test_goal_4_impossible():
    print(f"\n{CYAN}{BOLD}--- Test 4: Impossible Goal (Non-Existent Tool Handling) ---{RESET}")
    script_path = BACKEND_DIR / "data" / "scripted" / "goal_4_impossible.json"
    with open(script_path, mode="r", encoding="utf-8") as f:
        decisions = json.load(f)

    planner = ScriptedPlanner(decisions)
    res = run_agent(
        goal="Use quantum_teleport_fix tool to automatically repair server hardware",
        planner=planner
    )

    print(f"Run status: {res.get('status')}")
    if res.get("status") != "invalid_planner_output":
        print(f"{RED}FAIL: Goal 4 expected status 'invalid_planner_output', got '{res.get('status')}'{RESET}")
        return False

    print(f"{GREEN}PASS: Goal 4 (Impossible Goal) gracefully halted with status 'invalid_planner_output'.{RESET}")
    return True


def run_all_tests():
    print("=" * 70)
    print(f" {BOLD}EchoInsight Agent Goal Types & Tool Test Suite{RESET}")
    print("=" * 70)

    test_results = [
        ("get_feedback_trend Tool Test", test_get_feedback_trend_tool()),
        ("Goal 1: Full PRD & Backlog Pipeline", test_goal_1_full_pipeline()),
        ("Goal 2: Targeted Topic Backlog Item", test_goal_2_topic_backlog()),
        ("Goal 3: Read-Only Trend Query", test_goal_3_read_only_trend()),
        ("Goal 4: Impossible Goal Handling", test_goal_4_impossible()),
    ]

    print("\n" + "=" * 70)
    print(f" {BOLD}TEST RESULTS SUMMARY{RESET}")
    print("=" * 70)

    all_passed = True
    for name, passed in test_results:
        status_text = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  - {name:<45} : {status_text}")
        if not passed:
            all_passed = False

    print("=" * 70 + "\n")

    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
