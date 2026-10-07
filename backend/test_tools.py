"""
backend/test_tools.py

Isolated test suite for EchoInsight agent tools.

==============================================================================
WHAT IS THIS SCRIPT FOR? (FOR BEGINNERS)
==============================================================================
This test suite executes each tool in a natural workflow sequence:
1. Load sample feedback items from CSV (get_customer_feedback)
2. Search vector memory for relevant past issues (search_memory)
3. Cluster feedback into RICE prioritized groups (cluster_feedback_tool)
4. Rank the clusters by RICE score (rank_clusters)
5. Generate a Product Requirements Document (generate_prd_tool)
6. Save a ticket to the engineering backlog (create_backlog_item)
7. Verify the ticket was stored in backlog.json (verify_backlog_item)
8. Demonstrate failure simulation & recovery mode (SIMULATE_FAILURES)

If any step fails, it is marked FAIL (or SKIPPED if dependent) without hiding
failures with mock fallback data. It concludes with a summary table and an
overall result of PASS only if every tool passes.
==============================================================================
"""

import os
import sys
import time
from pathlib import Path

# Add backend root directory to Python path so app imports resolve properly
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.agent.tools import (
    SIMULATE_FAILURES,
    TOOL_REGISTRY,
    cluster_feedback_tool,
    create_backlog_item,
    generate_prd_tool,
    get_customer_feedback,
    rank_clusters,
    search_memory,
    verify_backlog_item,
)
import app.agent.tools as tools_module


def print_step_header(step_num: int, title: str) -> None:
    print("\n" + "=" * 70)
    print(f" STEP {step_num}: {title}")
    print("=" * 70)


def execute_with_test_retry(tool_fn, *args, **kwargs) -> dict:
    """
    Test helper function that executes a tool. If the tool returns ok=False with retryable=True,
    it prints 'Rate limited, waiting N seconds...', sleeps N+2 seconds, and retries the step once.

    NOTE: The tools themselves do NOT sleep or retry; this retry helper is only in test_tools.py.
    """
    result = tool_fn(*args, **kwargs)
    if not result.get("ok") and result.get("retryable"):
        n_seconds = result.get("retry_after_seconds")
        if n_seconds is None:
            n_seconds = 30
        print(f"Rate limited, waiting {n_seconds} seconds...")
        time.sleep(n_seconds + 2)
        print("  [Test Retry] Retrying tool step execution now...")
        result = tool_fn(*args, **kwargs)
    return result


def main():
    print("=== Starting EchoInsight Agent Tools Verification Test Suite ===")

    # Track results per tool: "PASS", "FAIL", or "SKIPPED"
    tool_results = {}
    tool_details = {}

    # --------------------------------------------------------------------------
    # Step 1: Read Sample Customer Feedback
    # --------------------------------------------------------------------------
    print_step_header(1, "Testing get_customer_feedback()")
    res1 = execute_with_test_retry(get_customer_feedback)
    if res1["ok"]:
        feedback_lines = res1["data"]
        tool_results["get_customer_feedback"] = "PASS"
        tool_details["get_customer_feedback"] = f"Loaded {len(feedback_lines)} items"
        print(f"  [Status] PASS | {tool_details['get_customer_feedback']}")
    else:
        feedback_lines = []
        tool_results["get_customer_feedback"] = "FAIL"
        tool_details["get_customer_feedback"] = f"Error: {res1.get('error')[:40]}..."
        print(f"  [Status] FAIL | {res1.get('error')}")

    # --------------------------------------------------------------------------
    # Step 2: Search Vector Memory
    # --------------------------------------------------------------------------
    print_step_header(2, "Testing search_memory()")
    res2 = execute_with_test_retry(search_memory, query="checkout credit card failure", top_k=3)
    if res2["ok"]:
        matches = res2["data"]
        tool_results["search_memory"] = "PASS"
        tool_details["search_memory"] = f"Found {len(matches)} vector matches"
        print(f"  [Status] PASS | {tool_details['search_memory']}")
    else:
        tool_results["search_memory"] = "FAIL"
        tool_details["search_memory"] = f"Error: {res2.get('error')[:40]}..."
        print(f"  [Status] FAIL | {res2.get('error')}")

    # --------------------------------------------------------------------------
    # Step 3: Cluster Feedback using Gemini AI
    # --------------------------------------------------------------------------
    print_step_header(3, "Testing cluster_feedback_tool()")
    clusters = None
    if tool_results.get("get_customer_feedback") == "PASS" and feedback_lines:
        test_lines = feedback_lines[:5]
        print(f"  [Action] Sending {len(test_lines)} feedback lines to Gemini AI for clustering...")
        res3 = execute_with_test_retry(cluster_feedback_tool, test_lines)
        if res3["ok"]:
            clusters = res3["data"]
            tool_results["cluster_feedback_tool"] = "PASS"
            tool_details["cluster_feedback_tool"] = f"Created {len(clusters)} clusters"
            print(f"  [Status] PASS | {tool_details['cluster_feedback_tool']}")
        else:
            tool_results["cluster_feedback_tool"] = "FAIL"
            tool_details["cluster_feedback_tool"] = f"Error ({res3.get('error_type')}): {res3.get('error')[:40]}..."
            print(f"  [Status] FAIL | Error Type: {res3.get('error_type')} | Message: {res3.get('error')}")
    else:
        tool_results["cluster_feedback_tool"] = "SKIPPED"
        tool_details["cluster_feedback_tool"] = "Depended on get_customer_feedback"
        print("  [Status] SKIPPED | Depends on get_customer_feedback")

    # --------------------------------------------------------------------------
    # Step 4: Rank Clusters by RICE Score
    # --------------------------------------------------------------------------
    print_step_header(4, "Testing rank_clusters()")
    top_cluster = None
    if clusters is not None:
        res4 = execute_with_test_retry(rank_clusters, clusters)
        if res4["ok"]:
            ranked_clusters = res4["data"]
            top_cluster = ranked_clusters[0] if ranked_clusters else None
            tool_results["rank_clusters"] = "PASS"
            score = top_cluster.get('rice_score', 0) if top_cluster else 0
            tool_details["rank_clusters"] = f"Ranked {len(ranked_clusters)} clusters (Top score: {score:.1f})"
            print(f"  [Status] PASS | {tool_details['rank_clusters']}")
        else:
            tool_results["rank_clusters"] = "FAIL"
            tool_details["rank_clusters"] = f"Error: {res4.get('error')[:40]}..."
            print(f"  [Status] FAIL | {res4.get('error')}")
    else:
        tool_results["rank_clusters"] = "SKIPPED"
        tool_details["rank_clusters"] = "Depended on cluster_feedback_tool"
        print("  [Status] SKIPPED | Depends on cluster_feedback_tool")

    # --------------------------------------------------------------------------
    # Step 5: Generate PRD for Top Ranked Cluster
    # --------------------------------------------------------------------------
    print_step_header(5, "Testing generate_prd_tool()")
    prd_data = None
    if top_cluster is not None:
        print(f"  [Action] Generating PRD for cluster '{top_cluster.get('theme_name')}'...")
        res5 = execute_with_test_retry(generate_prd_tool, top_cluster)
        if res5["ok"]:
            prd_data = res5["data"]
            tool_results["generate_prd_tool"] = "PASS"
            tool_details["generate_prd_tool"] = f"Title: '{prd_data.get('title')}'"
            print(f"  [Status] PASS | {tool_details['generate_prd_tool']}")
        else:
            tool_results["generate_prd_tool"] = "FAIL"
            tool_details["generate_prd_tool"] = f"Error ({res5.get('error_type')}): {res5.get('error')[:40]}..."
            print(f"  [Status] FAIL | Error Type: {res5.get('error_type')} | Message: {res5.get('error')}")
    else:
        tool_results["generate_prd_tool"] = "SKIPPED"
        tool_details["generate_prd_tool"] = "Depended on rank_clusters"
        print("  [Status] SKIPPED | Depends on rank_clusters")

    # --------------------------------------------------------------------------
    # Step 6: Create Engineering Backlog Item
    # --------------------------------------------------------------------------
    print_step_header(6, "Testing create_backlog_item()")
    ticket_title = prd_data.get("title") if prd_data else "Fix Checkout Payment Failures"
    ticket_desc = prd_data.get("problem_statement") if prd_data else "User payment failures reported during checkout step."
    res6 = execute_with_test_retry(
        create_backlog_item,
        title=ticket_title,
        description=ticket_desc,
        priority="High"
    )
    if res6["ok"]:
        item_data = res6["data"]
        created_id = item_data.get("id")
        tool_results["create_backlog_item"] = "PASS"
        tool_details["create_backlog_item"] = f"Created ticket {created_id}"
        print(f"  [Status] PASS | {tool_details['create_backlog_item']}")
    else:
        created_id = None
        tool_results["create_backlog_item"] = "FAIL"
        tool_details["create_backlog_item"] = f"Error: {res6.get('error')[:40]}..."
        print(f"  [Status] FAIL | {res6.get('error')}")

    # --------------------------------------------------------------------------
    # Step 7: Verify Backlog Item Existence
    # --------------------------------------------------------------------------
    print_step_header(7, "Testing verify_backlog_item()")
    if created_id is not None:
        res7 = execute_with_test_retry(verify_backlog_item, item_id=created_id)
        if res7["ok"]:
            tool_results["verify_backlog_item"] = "PASS"
            tool_details["verify_backlog_item"] = f"Verified ticket {created_id} in backlog.json"
            print(f"  [Status] PASS | {tool_details['verify_backlog_item']}")
        else:
            tool_results["verify_backlog_item"] = "FAIL"
            tool_details["verify_backlog_item"] = f"Error: {res7.get('error')[:40]}..."
            print(f"  [Status] FAIL | {res7.get('error')}")
    else:
        tool_results["verify_backlog_item"] = "SKIPPED"
        tool_details["verify_backlog_item"] = "Depended on create_backlog_item"
        print("  [Status] SKIPPED | Depends on create_backlog_item")

    # --------------------------------------------------------------------------
    # Step 8: Test Failure Recovery Mode (SIMULATE_FAILURES = True)
    # --------------------------------------------------------------------------
    print_step_header(8, "Testing Failure Recovery Mode (SIMULATE_FAILURES = True)")
    tools_module.SIMULATE_FAILURES = True
    tools_module._first_failure_occurred = False

    fail_res = create_backlog_item(title="Test Ticket", description="Test", priority="Low")
    retry_res = create_backlog_item(title="Test Ticket Retry", description="Test Retry", priority="Low")

    tools_module.SIMULATE_FAILURES = False

    if not fail_res.get("ok") and fail_res.get("retryable") and retry_res.get("ok"):
        tool_results["simulate_failures_demo"] = "PASS"
        tool_details["simulate_failures_demo"] = "Caught timeout & retried successfully"
        print("  [Status] PASS | Caught expected timeout & retried successfully")
    else:
        tool_results["simulate_failures_demo"] = "FAIL"
        tool_details["simulate_failures_demo"] = "Failure recovery simulation failed"
        print("  [Status] FAIL | Failure recovery simulation did not behave as expected")

    # --------------------------------------------------------------------------
    # Final Summary Table Output
    # --------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("                 AGENT TOOLS VERIFICATION SUMMARY")
    print("=" * 70)
    print(f" {'Tool Name':<28} | {'Status':<8} | Details")
    print("-" * 70)
    for tool_name, status in tool_results.items():
        details = tool_details.get(tool_name, "")
        print(f" {tool_name:<28} | {status:<8} | {details}")
    print("-" * 70)

    all_passed = all(status == "PASS" for status in tool_results.values())
    passed_count = sum(1 for status in tool_results.values() if status == "PASS")
    failed_count = sum(1 for status in tool_results.values() if status == "FAIL")
    skipped_count = sum(1 for status in tool_results.values() if status == "SKIPPED")

    if all_passed:
        print(f" OVERALL RESULT: PASS (All {len(tool_results)} tests passed)")
    else:
        print(f" OVERALL RESULT: FAIL ({passed_count} passed, {failed_count} failed, {skipped_count} skipped)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
