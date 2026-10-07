"""
backend/app/agent/tools.py

Tool layer for an autonomous AI agent in EchoInsight.

==============================================================================
WHAT IS A TOOL LAYER? (FOR BEGINNERS)
==============================================================================
An AI agent needs ways to interact with the world — like reading files, searching
databases, calling AI models, and creating tickets in external systems.

In AI development, a "Tool" is simply a standard Python function wrapped with:
1. Uniform Return Envelopes: Every tool returns {"ok": True, "data": ...} on success,
   or {"ok": False, "error": "..."} on failure. This ensures the AI agent can safely
   check if an action succeeded without crashing on unexpected exceptions.
2. Self-Contained Error Handling: Tools catch their own errors so the agent loop
   remains stable and can attempt recovery strategies when things fail.
3. Tool Registry Metadata: Descriptions and argument definitions that help an LLM
   understand what each tool does and when to call it.
==============================================================================
"""

import csv
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import existing domain models and service functions
from ..models import FeedbackCluster
from ..services.clustering_service import cluster_feedback
from ..services.embedding_service import get_embedding
from ..services.prd_service import generate_prd
from ..services.vector_store_service import find_similar_feedback

# Resolve paths to backend data directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
SAMPLE_FEEDBACK_PATH = DATA_DIR / "sample_feedback.csv"
BACKLOG_PATH = DATA_DIR / "backlog.json"

# ==============================================================================
# Simulation Control Flags (for demoing failure recovery)
# ==============================================================================
SIMULATE_FAILURES: bool = False
_first_failure_occurred: bool = False


# ==============================================================================
# Error Classification & Failure Envelope Helper
# ==============================================================================
def classify_error(message: str) -> Dict[str, Any]:
    """
    Analyzes an error message to determine if it is temporary/retryable
    and extracts or estimates the recommended retry delay (in seconds).

    Beginner explanation:
    Not all errors are equal! A 'File Not Found' error is permanent, but a '429 Rate Limit'
    or 'Timeout' is temporary. This helper checks if an error message contains rate limit,
    quota, or timeout keywords, and calculates how many seconds the caller should wait
    before retrying.

    Args:
        message (str): The raw error message string.

    Returns:
        dict: {"retryable": bool, "retry_after_seconds": int | None}
    """
    if not message or not isinstance(message, str):
        return {"retryable": False, "retry_after_seconds": None}

    msg_lower = message.lower()

    # Keywords indicating a temporary, quota, or rate-limited error
    retryable_keywords = ["429", "quota", "rate limit", "timed out", "timeout", "503"]
    is_retryable = any(kw in msg_lower for kw in retryable_keywords)

    if not is_retryable:
        return {"retryable": False, "retry_after_seconds": None}

    delay_seconds: Optional[float] = None

    # Pattern 1: "retry in 44.45s", "retry in 44.45 s", "retry in 44 seconds"
    match_retry_in = re.search(r"retry\s+in\s+([\d\.]+)\s*s?", msg_lower)
    if match_retry_in:
        try:
            delay_seconds = float(match_retry_in.group(1))
        except ValueError:
            pass

    # Pattern 2: "seconds: 44", "seconds: 28505"
    if delay_seconds is None:
        match_seconds = re.search(r"seconds:\s*([\d\.]+)", msg_lower)
        if match_seconds:
            try:
                delay_seconds = float(match_seconds.group(1))
            except ValueError:
                pass

    if delay_seconds is not None and delay_seconds > 0:
        retry_after = math.ceil(delay_seconds)
    else:
        # Default retry delay if retryable but no specific delay parsed from message
        retry_after = 30

    return {
        "retryable": True,
        "retry_after_seconds": retry_after
    }


def make_failure_envelope(error_message: str) -> Dict[str, Any]:
    """
    Constructs a standardized failure envelope dictionary containing classification metrics.

    Returns:
        Dict: {
            "ok": False,
            "error": error_message,
            "retryable": bool,
            "retry_after_seconds": int | None
        }
    """
    info = classify_error(error_message)
    return {
        "ok": False,
        "error": str(error_message),
        "retryable": info["retryable"],
        "retry_after_seconds": info["retry_after_seconds"]
    }


# ==============================================================================
# Tool 1: Get Customer Feedback
# ==============================================================================
def get_customer_feedback() -> Dict[str, Any]:
    """
    Reads sample customer feedback items from backend/data/sample_feedback.csv.

    Beginner explanation:
    This tool opens the sample feedback CSV file, reads each line from the 'feedback'
    column, and returns them as a Python list of strings inside a standard envelope.

    Returns:
        Dict envelope: {"ok": True, "data": list[str]} or failure envelope with retry metadata
    """
    try:
        if not SAMPLE_FEEDBACK_PATH.exists():
            return make_failure_envelope(f"Sample feedback file not found at {SAMPLE_FEEDBACK_PATH}")

        feedback_lines: List[str] = []
        with open(SAMPLE_FEEDBACK_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = row.get("feedback", "").strip()
                if text:
                    feedback_lines.append(text)

        return {"ok": True, "data": feedback_lines}

    except Exception as e:
        return make_failure_envelope(f"Failed to read customer feedback: {str(e)}")



# ==============================================================================
# Tool 2: Search Vector Memory
# ==============================================================================
def search_memory(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Searches long-term vector database (ChromaDB) for feedback items semantically
    similar to a search query.

    Beginner explanation:
    This tool converts the text query into a numerical embedding vector, then queries
    ChromaDB to find past feedback with similar semantic meaning.

    Args:
        query (str): The search text query.
        top_k (int): Maximum number of similar items to retrieve (default: 5).

    Returns:
        Dict envelope: {"ok": True, "data": list[dict]} or failure envelope with retry metadata
    """
    try:
        if not query or not isinstance(query, str) or not query.strip():
            return make_failure_envelope("Query string must not be empty.")

        # Step 1: Generate embedding vector for the search query
        query_embedding = get_embedding(query.strip())

        # Step 2: Query ChromaDB vector database
        matches = find_similar_feedback(embedding=query_embedding, top_k=top_k)

        return {"ok": True, "data": matches}

    except Exception as e:
        return make_failure_envelope(f"Failed to search vector memory: {str(e)}")


# ==============================================================================
# Tool 3: Cluster Feedback Tool
# ==============================================================================
def cluster_feedback_tool(feedback_lines: List[str]) -> Dict[str, Any]:
    """
    Groups a list of raw feedback text lines into prioritized thematic clusters using Gemini AI.

    Beginner explanation:
    This tool combines feedback strings into a single block of text and sends it to
    our existing Gemini clustering service. It converts the output Pydantic clusters
    into plain dictionary format for the agent.

    Args:
        feedback_lines (List[str]): List of raw feedback text strings.

    Returns:
        Dict envelope: {"ok": True, "data": list[dict]} or failure envelope with retry metadata
    """
    try:
        if not feedback_lines or not isinstance(feedback_lines, list):
            return make_failure_envelope("feedback_lines must be a non-empty list of strings.")

        # Join feedback lines with newlines
        raw_feedback_text = "\n".join([str(line) for line in feedback_lines if line])
        if not raw_feedback_text.strip():
            return make_failure_envelope("No valid feedback text provided to cluster.")

        # Call existing clustering service
        clusters = cluster_feedback(raw_feedback_text)

        # Convert Pydantic FeedbackCluster objects to plain dicts using model_dump()
        clusters_data = [cluster.model_dump() for cluster in clusters]

        return {"ok": True, "data": clusters_data}

    except Exception as e:
        return make_failure_envelope(f"Failed to cluster feedback: {str(e)}")


# ==============================================================================
# Tool 4: Rank Clusters
# ==============================================================================
def rank_clusters(clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sorts a list of feedback cluster dictionaries by RICE score in descending order.

    Beginner explanation:
    RICE score measures overall business priority (Reach * Impact * Confidence / Effort).
    This tool takes cluster dictionaries and sorts them so the highest impact feature
    opportunity is first.

    Args:
        clusters (List[Dict[str, Any]]): List of cluster dictionaries.

    Returns:
        Dict envelope: {"ok": True, "data": list[dict]} or failure envelope with retry metadata
    """
    try:
        if not isinstance(clusters, list):
            return make_failure_envelope("clusters parameter must be a list.")

        # Sort clusters by rice_score (highest first)
        ranked = sorted(
            clusters,
            key=lambda c: float(c.get("rice_score", 0.0)) if isinstance(c, dict) else 0.0,
            reverse=True
        )

        return {"ok": True, "data": ranked}

    except Exception as e:
        return make_failure_envelope(f"Failed to rank clusters: {str(e)}")


# ==============================================================================
# Tool 5: Generate PRD Tool
# ==============================================================================
def generate_prd_tool(cluster: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a Product Requirements Document (PRD) from a feedback cluster dictionary.

    Beginner explanation:
    This tool converts a cluster dictionary back into a FeedbackCluster Pydantic model,
    calls Gemini AI to draft user stories, acceptance criteria, and KPIs, and returns
    the PRD as a plain dictionary.

    Args:
        cluster (Dict[str, Any]): A single FeedbackCluster dictionary.

    Returns:
        Dict envelope: {"ok": True, "data": dict} or failure envelope with retry metadata
    """
    try:
        if not cluster or not isinstance(cluster, dict):
            return make_failure_envelope("cluster parameter must be a valid dictionary.")

        # Rebuild FeedbackCluster Pydantic model from dictionary
        cluster_model = FeedbackCluster(**cluster)

        # Call existing PRD generation service
        prd_model = generate_prd(cluster_model)

        # Return PRD as a dictionary using model_dump()
        return {"ok": True, "data": prd_model.model_dump()}

    except Exception as e:
        return make_failure_envelope(f"Failed to generate PRD: {str(e)}")


# ==============================================================================
# Tool 6: Create Backlog Item
# ==============================================================================
def create_backlog_item(title: str, description: str, priority: str) -> Dict[str, Any]:
    """
    Appends a new engineering ticket to backend/data/backlog.json.

    Beginner explanation:
    This tool saves engineered tasks to a local JSON file simulating an issue tracker
    like Jira or GitHub Issues. It assigns an incremental ticket ID (e.g., ENG-101),
    sets status to 'Open', and attaches a UTC timestamp.

    Note on SIMULATE_FAILURES:
    When SIMULATE_FAILURES is True, the first invocation intentionally raises a
    TimeoutError to demonstrate agent failure recovery capabilities.

    Args:
        title (str): Summary title of the backlog item.
        description (str): Detailed description or problem statement.
        priority (str): Priority rating ("High", "Medium", or "Low").

    Returns:
        Dict envelope: {"ok": True, "data": dict} or failure envelope with retry metadata
    """
    global _first_failure_occurred

    try:
        # Check simulation flag for intentional failure recovery testing
        if SIMULATE_FAILURES and not _first_failure_occurred:
            _first_failure_occurred = True
            raise TimeoutError("Backlog API timed out")

        # Input validation
        if not title or not isinstance(title, str):
            return make_failure_envelope("Title string is required.")
        if not description or not isinstance(description, str):
            return make_failure_envelope("Description string is required.")

        # Ensure directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing backlog items
        existing_items: List[Dict[str, Any]] = []
        if BACKLOG_PATH.exists():
            try:
                with open(BACKLOG_PATH, mode="r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        existing_items = json.loads(content)
            except Exception:
                existing_items = []

        # Determine next incremental ID (e.g., ENG-101, ENG-102)
        max_id_num = 100
        for item in existing_items:
            item_id = str(item.get("id", ""))
            if item_id.startswith("ENG-"):
                try:
                    num = int(item_id.split("-")[1])
                    if num > max_id_num:
                        max_id_num = num
                except ValueError:
                    pass

        new_id = f"ENG-{max_id_num + 1}"

        # Construct new ticket object
        new_item = {
            "id": new_id,
            "title": title.strip(),
            "description": description.strip(),
            "priority": priority.strip() if priority else "Medium",
            "status": "Open",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Save back to backlog.json
        existing_items.append(new_item)
        with open(BACKLOG_PATH, mode="w", encoding="utf-8") as f:
            json.dump(existing_items, f, indent=2)

        return {"ok": True, "data": new_item}

    except Exception as e:
        return make_failure_envelope(str(e))


# ==============================================================================
# Tool 7: Verify Backlog Item
# ==============================================================================
def verify_backlog_item(item_id: str) -> Dict[str, Any]:
    """
    Reads backend/data/backlog.json to verify that a ticket with item_id exists.

    Beginner explanation:
    This tool looks up a ticket in our local JSON backlog file by its ID (e.g. ENG-101)
    to confirm it was successfully created and persisted.

    Args:
        item_id (str): Unique ticket ID to verify (e.g., "ENG-101").

    Returns:
        Dict envelope: {"ok": True, "data": dict} or failure envelope with retry metadata
    """
    try:
        if not item_id or not isinstance(item_id, str):
            return make_failure_envelope("item_id string is required.")

        if not BACKLOG_PATH.exists():
            return make_failure_envelope(f"Backlog item '{item_id}' not found (backlog file does not exist).")

        with open(BACKLOG_PATH, mode="r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return make_failure_envelope(f"Backlog item '{item_id}' not found (backlog file is empty).")
            items: List[Dict[str, Any]] = json.loads(content)

        # Search for ticket matching item_id
        for item in items:
            if item.get("id") == item_id.strip():
                return {"ok": True, "data": item}

        return make_failure_envelope(f"Backlog item '{item_id}' not found.")

    except Exception as e:
        return make_failure_envelope(f"Failed to verify backlog item: {str(e)}")



# ==============================================================================
# Tool Registry Mapping
# ==============================================================================
# Maps every tool function name to its callable, documentation, parameters,
# and approval requirements (True ONLY for create_backlog_item).
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "get_customer_feedback": {
        "function": get_customer_feedback,
        "description": "Reads raw customer feedback lines from sample storage CSV.",
        "args": {},
        "requires_approval": False
    },
    "search_memory": {
        "function": search_memory,
        "description": "Searches ChromaDB vector memory for feedback semantically similar to a query.",
        "args": {
            "query": "str: Natural language search text query",
            "top_k": "int: Maximum number of similar items to return (default 5)"
        },
        "requires_approval": False
    },
    "cluster_feedback_tool": {
        "function": cluster_feedback_tool,
        "description": "Groups feedback lines into thematic RICE clusters using Gemini AI.",
        "args": {
            "feedback_lines": "list[str]: List of customer feedback text lines"
        },
        "requires_approval": False
    },
    "rank_clusters": {
        "function": rank_clusters,
        "description": "Ranks feedback cluster dictionaries by RICE score in descending order.",
        "args": {
            "clusters": "list[dict]: List of cluster dictionaries to rank"
        },
        "requires_approval": False
    },
    "generate_prd_tool": {
        "function": generate_prd_tool,
        "description": "Generates a complete Product Requirements Document (PRD) from a feedback cluster dictionary.",
        "args": {
            "cluster": "dict: FeedbackCluster dictionary for which to write a PRD"
        },
        "requires_approval": False
    },
    "create_backlog_item": {
        "function": create_backlog_item,
        "description": "Creates a new engineering ticket in the local backlog storage file. Requires explicit approval.",
        "args": {
            "title": "str: Clear summary title for the backlog item",
            "description": "str: Detailed problem statement or feature requirement",
            "priority": "str: Priority rating (High, Medium, or Low)"
        },
        "requires_approval": True
    },
    "verify_backlog_item": {
        "function": verify_backlog_item,
        "description": "Verifies that an engineering ticket with the given ID exists in local backlog storage.",
        "args": {
            "item_id": "str: Unique ticket ID (e.g. ENG-101)"
        },
        "requires_approval": False
    }
}
