"""
backend/test_agent_loop.py

STAND-IN PLANNER TESTS (loop mechanics only, not LLM reasoning)

==============================================================================
WHAT IS THIS TEST SUITE FOR? (FOR BEGINNERS)
==============================================================================
This test suite verifies the core autonomous Agent Loop mechanics in complete
isolation using ScriptedPlanner (deterministic pre-scripted decisions) and a fake
human approval handler.

It does NOT make any live LLM or Gemini API calls. All sleep delays are mocked out
using sleep_fn=lambda s: None so the entire suite runs in milliseconds.

Scenarios Tested:
1. Happy Path: Complete end-to-end workflow execution.
2. Transient Failure Recovery: Retries temporary timeouts (SIMULATE_FAILURES=True).
3. Quota Exhaustion: Halts loop immediately on non-retryable quota exhaustion.
4. Approval Rejection: Refuses tool execution when human supervisor rejects.
5. Unknown Tool Recovery: Recovers cleanly when planner outputs invalid tool name.
6. Verification Guard: Refuses finish until created backlog items are verified.
7. Step Cap Enforcement: Stops loop when max_steps limit is reached.
==============================================================================
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent.loop import run_agent
from app.agent.planner import ScriptedPlanner
from app.agent.tools import (
    SIMULATE_FAILURES,
    TOOL_REGISTRY,
    create_backlog_item,
    verify_backlog_item,
)
import app.agent.tools as tools_module


# Instant sleep function for zero-wait test execution
INSTANT_SLEEP = lambda seconds: None


def print_test_header(test_num: int, title: str) -> None:
    print("\n" + "=" * 75)
    print(f" TEST {test_num}: {title}")
    print("=" * 75)


def test_happy_path() -> tuple[bool, str]:
    """Test 1: Happy Path - Complete Workflow Execution"""
    decisions = [
        {
            "action": "tool",
            "tool": "get_customer_feedback",
            "args": {},
            "reason": "Fetch raw feedback lines."
        },
        {
            "action": "tool",
            "tool": "create_backlog_item",
            "args": {"title": "Test Happy Path Ticket", "description": "Fix bug", "priority": "High"},
            "reason": "Create backlog ticket."
        },
        {
            "action": "tool",
            "tool": "verify_backlog_item",
            "args": {"item_id": "$LAST_CREATED_ID"},

            "reason": "Verify created item."
        },
        {
            "action": "finish",
            "tool": "",
            "args": {},
            "reason": "All tasks completed.",
            "final_answer": "Happy path execution completed successfully."
        }
    ]

    planner = ScriptedPlanner(decisions)
    always_approve = lambda tool, args, reason: True

    res = run_agent(
        goal="Process customer feedback and create verified ticket",
        planner=planner,
        approval_handler=always_approve,
        max_steps=10,
        sleep_fn=INSTANT_SLEEP
    )

    passed = res.get("status") == "completed" and res.get("steps") == 4
    details = f"Status: {res.get('status')} | Steps: {res.get('steps')}"
    return passed, details


def test_transient_failure_recovery() -> tuple[bool, str]:
    """Test 2: Transient Failure Recovery via SIMULATE_FAILURES"""
    tools_module.SIMULATE_FAILURES = True
    tools_module._first_failure_occurred = False

    decisions = [
        {
            "action": "tool",
            "tool": "create_backlog_item",
            "args": {"title": "Timeout Recovery Ticket", "description": "Desc", "priority": "Medium"},
            "reason": "Create backlog item (will trigger simulated timeout on 1st call)."
        },
        {
            "action": "tool",
            "tool": "verify_backlog_item",
            "args": {"item_id": "$LAST_CREATED_ID"},
            "reason": "Verify ticket."
        },

        {
            "action": "finish",
            "tool": "",
            "args": {},
            "reason": "Task complete.",
            "final_answer": "Transient failure recovery successful."
        }
    ]

    planner = ScriptedPlanner(decisions)
    always_approve = lambda tool, args, reason: True

    res = run_agent(
        goal="Test transient failure retry loop",
        planner=planner,
        approval_handler=always_approve,
        max_steps=10,
        sleep_fn=INSTANT_SLEEP
    )

    tools_module.SIMULATE_FAILURES = False

    # Check that retry event was recorded in trace
    retry_events = [e for e in res.get("trace", []) if e.get("event_type") == "retry"]

    passed = res.get("status") == "completed" and len(retry_events) == 1
    details = f"Status: {res.get('status')} | Retries Recorded in Trace: {len(retry_events)}"
    return passed, details


def test_quota_exhausted_halts() -> tuple[bool, str]:
    """Test 3: Quota Exhausted Halts Loop Immediately"""
    # Temporarily register a mock tool that returns quota_exhausted error
    def mock_quota_tool() -> dict:
        return {
            "ok": False,
            "error": "429 You exceeded your current daily quota.",
            "retryable": False,
            "error_type": "quota_exhausted",
            "retry_after_seconds": 28000
        }

    original_tool = TOOL_REGISTRY.get("get_customer_feedback")
    TOOL_REGISTRY["get_customer_feedback"] = {
        "function": mock_quota_tool,
        "description": "Mock quota tool",
        "args": {},
        "requires_approval": False
    }

    decisions = [
        {
            "action": "tool",
            "tool": "get_customer_feedback",
            "args": {},
            "reason": "Try fetching feedback (will fail with quota_exhausted)."
        }
    ]

    planner = ScriptedPlanner(decisions)
    res = run_agent(
        goal="Test quota exhaustion halting",
        planner=planner,
        max_steps=10,
        sleep_fn=INSTANT_SLEEP
    )

    # Restore original tool
    if original_tool:
        TOOL_REGISTRY["get_customer_feedback"] = original_tool

    passed = res.get("status") == "halted_quota"
    details = f"Status: {res.get('status')} | Final Answer: {res.get('final_answer')[:60]}..."
    return passed, details


def test_approval_rejected() -> tuple[bool, str]:
    """Test 4: Approval Rejected by Human Supervisor"""
    decisions = [
        {
            "action": "tool",
            "tool": "create_backlog_item",
            "args": {"title": "Unapproved Ticket", "description": "Desc", "priority": "Low"},
            "reason": "Create ticket requiring approval."
        },
        {
            "action": "finish",
            "tool": "",
            "args": {},
            "reason": "Supervisor rejected ticket creation.",
            "final_answer": "Task terminated following human approval rejection."
        }
    ]

    planner = ScriptedPlanner(decisions)
    always_reject = lambda tool, args, reason: False

    res = run_agent(
        goal="Test human rejection handling",
        planner=planner,
        approval_handler=always_reject,
        max_steps=10,
        sleep_fn=INSTANT_SLEEP
    )

    # Verify approval_result event was recorded with approved=False
    rejection_events = [e for e in res.get("trace", []) if e.get("event_type") == "approval_result" and not e.get("approved")]

    passed = res.get("status") == "rejected_by_human" and len(rejection_events) == 1
    details = f"Status: {res.get('status')} | Rejections Logged: {len(rejection_events)}"
    return passed, details


def test_unknown_tool_recovery() -> tuple[bool, str]:
    """Test 5: Unknown Tool Decision Recovery"""
    decisions = [
        {
            "action": "tool",
            "tool": "non_existent_fake_tool_xyz",
            "args": {},
            "reason": "Hallucinated tool name."
        },
        {
            "action": "tool",
            "tool": "get_customer_feedback",
            "args": {},
            "reason": "Recovered valid tool decision."
        },
        {
            "action": "finish",
            "tool": "",
            "args": {},
            "reason": "Task complete.",
            "final_answer": "Recovered from unknown tool error."
        }
    ]

    planner = ScriptedPlanner(decisions)
    res = run_agent(
        goal="Test recovery from unknown tool decision",
        planner=planner,
        max_steps=10,
        sleep_fn=INSTANT_SLEEP
    )

    passed = res.get("status") == "completed" and res.get("steps") == 3
    details = f"Status: {res.get('status')} | Total Steps: {res.get('steps')}"
    return passed, details


def test_finish_refused_before_verification() -> tuple[bool, str]:
    """Test 6: Verification Guard Refuses Finish Before Verification"""
    decisions = [
        {
            "action": "tool",
            "tool": "create_backlog_item",
            "args": {"title": "Verification Guard Ticket", "description": "Desc", "priority": "High"},
            "reason": "Create backlog ticket."
        },
        {
            "action": "finish",
            "tool": "",
            "args": {},
            "reason": "Premature finish attempt without calling verify_backlog_item.",
            "final_answer": "Premature finish."
        },
        {
            "action": "tool",
            "tool": "verify_backlog_item",
            "args": {"item_id": "$LAST_CREATED_ID"},
            "reason": "Now verifying item as forced by verification guard."
        },

        {
            "action": "finish",
            "tool": "",
            "args": {},
            "reason": "Finishing after verification.",
            "final_answer": "Verification completed."
        }
    ]

    planner = ScriptedPlanner(decisions)
    always_approve = lambda tool, args, reason: True

    res = run_agent(
        goal="Test verification guard enforcement",
        planner=planner,
        approval_handler=always_approve,
        max_steps=10,
        sleep_fn=INSTANT_SLEEP
    )

    # Check for verification refusal event in trace
    refusal_events = [e for e in res.get("trace", []) if e.get("event_type") == "verification" and not e.get("passed")]

    passed = res.get("status") == "completed" and len(refusal_events) >= 1
    details = f"Status: {res.get('status')} | Refusal Events Recorded: {len(refusal_events)}"
    return passed, details


def test_step_cap_reached() -> tuple[bool, str]:
    """Test 7: Step Cap Reached Halts Loop"""
    decisions = [
        {"action": "tool", "tool": "get_customer_feedback", "args": {}, "reason": "Step 1"},
        {"action": "tool", "tool": "get_customer_feedback", "args": {}, "reason": "Step 2"},
        {"action": "tool", "tool": "get_customer_feedback", "args": {}, "reason": "Step 3"},
    ]

    planner = ScriptedPlanner(decisions)
    res = run_agent(
        goal="Test step cap halting",
        planner=planner,
        max_steps=2,
        sleep_fn=INSTANT_SLEEP
    )

    passed = res.get("status") == "max_steps_reached" and res.get("steps") == 2
    details = f"Status: {res.get('status')} | Steps Executed: {res.get('steps')}"
    return passed, details


def main():
    print("=" * 75)
    print(" STAND-IN PLANNER TESTS (loop mechanics only, not LLM reasoning)")
    print("=" * 75)

    test_cases = [
        ("Happy Path Workflow", test_happy_path),
        ("Transient Failure Recovery", test_transient_failure_recovery),
        ("Quota Exhausted Halts Loop", test_quota_exhausted_halts),
        ("Approval Rejected by Human", test_approval_rejected),
        ("Unknown Tool Recovery", test_unknown_tool_recovery),
        ("Verification Guard Refusal", test_finish_refused_before_verification),
        ("Step Cap Reached Halts Loop", test_step_cap_reached),
    ]

    results = {}

    for idx, (name, test_func) in enumerate(test_cases, start=1):
        print_test_header(idx, f"Running {name}")
        try:
            passed, details = test_func()
            status_str = "PASS" if passed else "FAIL"
            results[name] = (status_str, details)
            print(f"  [Result] {status_str} | {details}")
        except Exception as e:
            results[name] = ("FAIL", f"Uncaught exception: {str(e)}")
            print(f"  [Result] FAIL | Exception: {str(e)}")

    print("\n" + "=" * 75)
    print("                 AGENT LOOP TEST SUMMARY TABLE")
    print("=" * 75)
    print(f" {'Test Case':<32} | {'Status':<8} | Details")
    print("-" * 75)
    for name, (status_str, details) in results.items():
        print(f" {name:<32} | {status_str:<8} | {details}")
    print("-" * 75)

    all_passed = all(status_str == "PASS" for status_str, _ in results.values())
    passed_cnt = sum(1 for status_str, _ in results.values() if status_str == "PASS")
    total_cnt = len(results)

    if all_passed:
        print(f" OVERALL RESULT: PASS ({passed_cnt}/{total_cnt} test cases passed)")
    else:
        print(f" OVERALL RESULT: FAIL ({passed_cnt}/{total_cnt} passed, {total_cnt - passed_cnt} failed)")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
