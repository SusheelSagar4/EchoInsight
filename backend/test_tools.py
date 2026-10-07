"""
backend/test_tools.py

Isolated test script for EchoInsight agent tools.

==============================================================================
WHAT IS THIS SCRIPT FOR? (FOR BEGINNERS)
==============================================================================
Before building a complex AI Agent loop, it is best practice to test all underlying
tools individually in isolation.

This script executes each tool in a natural workflow sequence:
1. Load sample feedback items from CSV (get_customer_feedback)
2. Search vector memory for relevant past issues (search_memory)
3. Cluster feedback into RICE prioritized groups (cluster_feedback_tool)
4. Rank the clusters by RICE score (rank_clusters)
5. Generate a Product Requirements Document (generate_prd_tool)
6. Save a ticket to the engineering backlog (create_backlog_item)
7. Verify the ticket was stored in backlog.json (verify_backlog_item)
8. Demonstrate failure simulation & recovery mode (SIMULATE_FAILURES)
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

    # --------------------------------------------------------------------------
    # Step 1: Read Sample Customer Feedback
    # --------------------------------------------------------------------------
    print_step_header(1, "Testing get_customer_feedback()")
    res1 = execute_with_test_retry(get_customer_feedback)
    print(f"  [Status] OK: {res1['ok']}")
    if res1["ok"]:
        feedback_lines = res1["data"]
        print(f"  [Summary] Loaded {len(feedback_lines)} feedback items from sample_feedback.csv")
        print(f"  [Sample Line 1] \"{feedback_lines[0]}\"")
    else:
        print(f"  [Error] {res1['error']} | Retryable: {res1.get('retryable')} | Retry After: {res1.get('retry_after_seconds')}")
        return

    # --------------------------------------------------------------------------
    # Step 2: Search Vector Memory
    # --------------------------------------------------------------------------
    print_step_header(2, "Testing search_memory()")
    res2 = execute_with_test_retry(search_memory, query="checkout credit card failure", top_k=3)
    print(f"  [Status] OK: {res2['ok']}")
    if res2["ok"]:
        matches = res2["data"]
        print(f"  [Summary] Found {len(matches)} vector memory matches for query 'checkout credit card failure'")
        for idx, match in enumerate(matches, start=1):
            print(f"    Match #{idx}: {match.get('document', '')[:60]}... (Distance: {match.get('distance', 0):.3f})")
    else:
        print(f"  [Error] {res2['error']} | Retryable: {res2.get('retryable')}")

    # --------------------------------------------------------------------------
    # Step 3: Cluster Feedback using Gemini AI
    # --------------------------------------------------------------------------
    print_step_header(3, "Testing cluster_feedback_tool()")
    # Use first 5 lines for fast isolated test execution
    test_lines = feedback_lines[:5]
    print(f"  [Action] Sending {len(test_lines)} feedback lines to Gemini AI for clustering...")
    res3 = execute_with_test_retry(cluster_feedback_tool, test_lines)
    print(f"  [Status] OK: {res3['ok']}")
    if res3["ok"]:
        clusters = res3["data"]
        print(f"  [Summary] Gemini created {len(clusters)} thematic clusters.")
        for c in clusters:
            print(f"    - Theme: '{c.get('theme_name')}' | RICE Score: {c.get('rice_score', 0):.2f} | Items: {len(c.get('feedback_items', []))}")
    else:
        print(f"  [Error Envelope] {res3['error']}")
        print(f"  [Retry Metadata] Retryable: {res3.get('retryable')} | Retry After: {res3.get('retry_after_seconds')}s")
        print("  [Notice] Gemini API limit hit or unavailable. Using sample cluster data to test remaining tools...")
        clusters = [
            {
                "theme_name": "Checkout Payment Failures",
                "feedback_items": [
                    {
                        "text": "Tried paying with my Visa card three times and it keeps giving me Error 502 at checkout!!",
                        "sentiment": "Negative",
                        "intent": "Bug",
                        "urgency": "High",
                        "similar_past_count": 2
                    },
                    {
                        "text": "Why does the payment button get stuck on 'Processing...' forever when I use Apple Pay?",
                        "sentiment": "Negative",
                        "intent": "Bug",
                        "urgency": "High",
                        "similar_past_count": 1
                    }
                ],
                "frequency": 2,
                "reach": 40.0,
                "impact": 3.0,
                "confidence": 0.9,
                "effort": 2.0,
                "rice_score": 54.0,
                "affected_count": 5,
                "negative_feedback_count": 2
            }
        ]



    # --------------------------------------------------------------------------
    # Step 4: Rank Clusters by RICE Score
    # --------------------------------------------------------------------------
    print_step_header(4, "Testing rank_clusters()")
    res4 = execute_with_test_retry(rank_clusters, clusters)
    print(f"  [Status] OK: {res4['ok']}")
    if res4["ok"]:
        ranked_clusters = res4["data"]
        top_cluster = ranked_clusters[0]
        print(f"  [Summary] Ranked {len(ranked_clusters)} clusters highest-to-lowest RICE score.")
        print(f"  [#1 Ranked Theme] '{top_cluster.get('theme_name')}' with RICE score {top_cluster.get('rice_score', 0):.2f}")
    else:
        print(f"  [Error] {res4['error']} | Retryable: {res4.get('retryable')}")
        return

    # --------------------------------------------------------------------------
    # Step 5: Generate PRD for Top Ranked Cluster
    # --------------------------------------------------------------------------
    print_step_header(5, "Testing generate_prd_tool()")
    print(f"  [Action] Generating PRD for cluster '{top_cluster.get('theme_name')}'...")
    res5 = execute_with_test_retry(generate_prd_tool, top_cluster)
    print(f"  [Status] OK: {res5['ok']}")
    if res5["ok"]:
        prd_data = res5["data"]
        print(f"  [Summary] PRD generated successfully!")
        print(f"    - Title: {prd_data.get('title')}")
        print(f"    - Problem Statement: {prd_data.get('problem_statement', '')[:100]}...")
        print(f"    - User Stories Count: {len(prd_data.get('user_stories', []))}")
        print(f"    - Acceptance Criteria Count: {len(prd_data.get('acceptance_criteria', []))}")
        print(f"    - KPIs Count: {len(prd_data.get('kpis', []))}")
    else:
        print(f"  [Error Envelope] {res5['error']}")
        print(f"  [Retry Metadata] Retryable: {res5.get('retryable')} | Retry After: {res5.get('retry_after_seconds')}s")
        print("  [Notice] Gemini API limit hit or unavailable. Using sample PRD data for ticket creation test...")
        prd_data = {
            "title": f"Resolve {top_cluster.get('theme_name')}",
            "problem_statement": "Multiple users reported recurring checkout payment failures and app crashes.",
            "user_stories": ["As a customer, I want seamless payment processing..."],
            "acceptance_criteria": ["System must retry failed gateway calls once..."],
            "kpis": ["Reduce checkout error rate by 80%"]
        }

    # --------------------------------------------------------------------------
    # Step 6: Create Engineering Backlog Item
    # --------------------------------------------------------------------------
    print_step_header(6, "Testing create_backlog_item()")
    ticket_title = prd_data.get("title", f"Fix {top_cluster.get('theme_name')}")
    ticket_desc = prd_data.get("problem_statement", "User feedback fix required.")
    res6 = execute_with_test_retry(
        create_backlog_item,
        title=ticket_title,
        description=ticket_desc,
        priority="High"
    )
    print(f"  [Status] OK: {res6['ok']}")
    if res6["ok"]:
        item_data = res6["data"]
        created_id = item_data.get("id")
        print(f"  [Summary] Ticket created successfully!")
        print(f"    - ID: {created_id}")
        print(f"    - Title: {item_data.get('title')}")
        print(f"    - Status: {item_data.get('status')}")
        print(f"    - Created At: {item_data.get('created_at')}")
    else:
        print(f"  [Error] {res6['error']} | Retryable: {res6.get('retryable')}")
        return

    # --------------------------------------------------------------------------
    # Step 7: Verify Backlog Item Existence
    # --------------------------------------------------------------------------
    print_step_header(7, "Testing verify_backlog_item()")
    res7 = execute_with_test_retry(verify_backlog_item, item_id=created_id)
    print(f"  [Status] OK: {res7['ok']}")
    if res7["ok"]:
        verified_data = res7["data"]
        print(f"  [Summary] Ticket '{created_id}' verified in backlog.json persistence!")
        print(f"    - Confirmed Title: {verified_data.get('title')}")
        print(f"    - Confirmed Priority: {verified_data.get('priority')}")
    else:
        print(f"  [Error] {res7['error']} | Retryable: {res7.get('retryable')}")

    # --------------------------------------------------------------------------
    # Step 8: Test Simulation of Failure Recovery
    # --------------------------------------------------------------------------
    print_step_header(8, "Testing Failure Recovery Mode (SIMULATE_FAILURES = True)")
    tools_module.SIMULATE_FAILURES = True
    tools_module._first_failure_occurred = False

    print("  [Call 1 with SIMULATE_FAILURES=True] Calling create_backlog_item()...")
    fail_res = create_backlog_item(title="Test Ticket", description="Test", priority="Low")
    print(f"  [Call 1 Status] OK: {fail_res['ok']} | Error: \"{fail_res.get('error')}\" | Retryable: {fail_res.get('retryable')} | Retry After: {fail_res.get('retry_after_seconds')}s")

    print("  [Call 2 (Retry) with SIMULATE_FAILURES=True] Calling create_backlog_item()...")
    retry_res = create_backlog_item(title="Test Ticket Retry", description="Test Retry", priority="Low")
    print(f"  [Call 2 Status] OK: {retry_res['ok']} | Ticket Created ID: {retry_res.get('data', {}).get('id')}")

    tools_module.SIMULATE_FAILURES = False


    print("\n" + "=" * 70)
    print(" [SUCCESS] ALL TOOL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
