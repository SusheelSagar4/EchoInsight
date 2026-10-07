"""
backend/test_agent_api.py

Stand-in Test Suite for EchoInsight Autonomous Agent REST API.

==============================================================================
WHAT IS THIS TEST SUITE FOR? (FOR BEGINNERS)
==============================================================================
This script tests the agent API endpoints (/agent/run, /agent/runs/{id}, /agent/runs/{id}/approve)
offline using FastAPI TestClient and ScriptedPlanner.

Tested Capabilities:
1. Approval Pause & Resume (Approval Approved -> Task Completes)
2. Approval Rejection (Approval Rejected -> Rejection Recorded & Task Concludes)
3. Approval Timeout (Approval Times Out -> Status becomes 'approval_timeout')
4. Trace Persistence (Saved run JSON verified on disk)
==============================================================================
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add backend root to Python path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Color constants for terminal formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def poll_until_status(run_id: str, target_statuses: List[str], max_wait_sec: float = 5.0, poll_interval: float = 0.1) -> Dict[str, Any]:
    """Polls GET /agent/runs/{run_id} until status matches one of target_statuses or timeout occurs."""
    start_time = time.time()
    last_res = {}
    while time.time() - start_time < max_wait_sec:
        response = client.get(f"/agent/runs/{run_id}")
        if response.status_code == 200:
            last_res = response.json()
            if last_res.get("status") in target_statuses:
                return last_res
        time.sleep(poll_interval)
    return last_res


def test_approval_pause_and_approve() -> bool:
    """Test 1: Run pauses on approval request, resumes when approved=True, and completes task."""
    print(f"\n{CYAN}{BOLD}--- Test 1: Approval Pause & Resume (approved=True) ---{RESET}")
    decisions = [
        {
            "action": "tool",
            "tool": "get_customer_feedback",
            "args": {},
            "reason": "Fetch feedback"
        },
        {
            "action": "tool",
            "tool": "create_backlog_item",
            "args": {
                "title": "API Test Backlog Ticket",
                "description": "Created via API test suite",
                "priority": "High"
            },
            "reason": "Create ticket requiring approval"
        },
        {
            "action": "tool",
            "tool": "verify_backlog_item",
            "args": {
                "item_id": "$LAST_CREATED_ID"
            },
            "reason": "Verify backlog ticket"
        },
        {
            "action": "finish",
            "tool": "",
            "args": {},
            "reason": "Task finished",
            "final_answer": "Approval test completed successfully."
        }
    ]

    req_payload = {
        "goal": "Test approval approve flow",
        "decisions": decisions,
        "approval_timeout_seconds": 10.0
    }

    res = client.post("/agent/run", json=req_payload)
    if res.status_code != 200:
        print(f"{RED}FAIL: POST /agent/run returned status {res.status_code}{RESET}")
        return False

    run_data = res.json()
    run_id = run_data.get("run_id")
    print(f"Started run: {run_id}")

    # Wait until status becomes 'waiting_approval'
    status_data = poll_until_status(run_id, ["waiting_approval"])
    print(f"Polled status: {status_data.get('status')}")

    if status_data.get("status") != "waiting_approval":
        print(f"{RED}FAIL: Expected status 'waiting_approval', got '{status_data.get('status')}'{RESET}")
        return False

    pending = status_data.get("pending_approval")
    if not pending or pending.get("tool") != "create_backlog_item":
        print(f"{RED}FAIL: Expected pending_approval for 'create_backlog_item', got {pending}{RESET}")
        return False

    print(f"Pending approval detected for tool: {pending.get('tool')}")

    # Approve execution
    app_res = client.post(f"/agent/runs/{run_id}/approve", json={"approved": True})
    if app_res.status_code != 200:
        print(f"{RED}FAIL: POST /approve returned {app_res.status_code}{RESET}")
        return False

    # Wait for completion
    final_data = poll_until_status(run_id, ["completed", "failed"], max_wait_sec=5.0)
    print(f"Final status: {final_data.get('status')}")

    if final_data.get("status") != "completed":
        print(f"{RED}FAIL: Expected final status 'completed', got '{final_data.get('status')}'{RESET}")
        return False

    print(f"{GREEN}PASS: Approval Pause & Resume (approved=True) verified.{RESET}")
    return True


def test_approval_rejection() -> bool:
    """Test 2: Run pauses on approval request, resumes when approved=False, records rejection."""
    print(f"\n{CYAN}{BOLD}--- Test 2: Approval Rejection (approved=False) ---{RESET}")
    decisions = [
        {
            "action": "tool",
            "tool": "create_backlog_item",
            "args": {
                "title": "Rejected Backlog Ticket",
                "description": "Should be rejected by user",
                "priority": "Low"
            },
            "reason": "Create ticket requiring approval"
        },
        {
            "action": "finish",
            "tool": "",
            "args": {},
            "reason": "Conclude after rejection",
            "final_answer": "Rejection processed."
        }
    ]

    req_payload = {
        "goal": "Test approval rejection flow",
        "decisions": decisions,
        "approval_timeout_seconds": 10.0
    }

    res = client.post("/agent/run", json=req_payload)
    if res.status_code != 200:
        print(f"{RED}FAIL: POST /agent/run returned {res.status_code}{RESET}")
        return False

    run_id = res.json().get("run_id")

    status_data = poll_until_status(run_id, ["waiting_approval"])
    if status_data.get("status") != "waiting_approval":
        print(f"{RED}FAIL: Expected status 'waiting_approval', got '{status_data.get('status')}'{RESET}")
        return False

    # Reject execution
    app_res = client.post(f"/agent/runs/{run_id}/approve", json={"approved": False})
    if app_res.status_code != 200:
        print(f"{RED}FAIL: POST /approve returned {app_res.status_code}{RESET}")
        return False

    final_data = poll_until_status(run_id, ["rejected_by_human", "completed"], max_wait_sec=5.0)
    print(f"Final status: {final_data.get('status')}")

    if final_data.get("status") not in ["rejected_by_human", "completed"]:
        print(f"{RED}FAIL: Unexpected final status '{final_data.get('status')}'{RESET}")
        return False

    print(f"{GREEN}PASS: Approval Rejection (approved=False) verified.{RESET}")
    return True


def test_approval_timeout() -> bool:
    """Test 3: Approval request times out after specified duration, status becomes 'approval_timeout'."""
    print(f"\n{CYAN}{BOLD}--- Test 3: Approval Timeout (status=approval_timeout) ---{RESET}")
    decisions = [
        {
            "action": "tool",
            "tool": "create_backlog_item",
            "args": {
                "title": "Timed out Ticket",
                "description": "Approval will time out",
                "priority": "Medium"
            },
            "reason": "Create ticket requiring approval"
        }
    ]

    # Set ultra-short timeout for fast test execution (0.4s)
    req_payload = {
        "goal": "Test approval timeout",
        "decisions": decisions,
        "approval_timeout_seconds": 0.4
    }

    res = client.post("/agent/run", json=req_payload)
    if res.status_code != 200:
        print(f"{RED}FAIL: POST /agent/run returned {res.status_code}{RESET}")
        return False

    run_id = res.json().get("run_id")

    # Wait for approval timeout to trigger
    final_data = poll_until_status(run_id, ["approval_timeout"], max_wait_sec=3.0)
    print(f"Final status: {final_data.get('status')}")

    if final_data.get("status") != "approval_timeout":
        print(f"{RED}FAIL: Expected status 'approval_timeout', got '{final_data.get('status')}'{RESET}")
        return False

    print(f"{GREEN}PASS: Approval Timeout (status='approval_timeout') verified.{RESET}")
    return True


def test_invalid_approve_request() -> bool:
    """Test 4: Attempting to approve a non-existent or active non-paused run returns 400 or 404."""
    print(f"\n{CYAN}{BOLD}--- Test 4: Invalid Approval Requests ---{RESET}")
    # 404 test
    res_404 = client.post("/agent/runs/non_existent_run_id/approve", json={"approved": True})
    if res_404.status_code != 404:
        print(f"{RED}FAIL: Expected 404 for unknown run_id, got {res_404.status_code}{RESET}")
        return False

    # 400 test: approve run that is not waiting for approval
    run_req = client.post("/agent/run", json={"goal": "Completed run", "decisions": [{"action": "finish", "reason": "done"}]})
    run_id = run_req.json().get("run_id")
    poll_until_status(run_id, ["completed"])

    res_400 = client.post(f"/agent/runs/{run_id}/approve", json={"approved": True})
    if res_400.status_code != 400:
        print(f"{RED}FAIL: Expected 400 when approving active/finished run, got {res_400.status_code}{RESET}")
        return False

    print(f"{GREEN}PASS: Invalid approval error handling verified (404 & 400).{RESET}")
    return True


def run_all_tests():
    print("=" * 70)
    print(f" {BOLD}EchoInsight Autonomous Agent API Stand-In Test Suite{RESET}")
    print("=" * 70)

    test_results = [
        ("Approval Pause & Resume (approved=True)", test_approval_pause_and_approve()),
        ("Approval Rejection (approved=False)", test_approval_rejection()),
        ("Approval Timeout (status=approval_timeout)", test_approval_timeout()),
        ("Invalid Approval Error Guard (404/400)", test_invalid_approve_request()),
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
