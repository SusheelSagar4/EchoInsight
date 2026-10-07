"""
backend/preflight.py

Preflight Diagnostic System Verification script for EchoInsight.
Performs live sanity checks for API key configuration, LLM text generation,
LLM JSON mode generation, vector embeddings, and ChromaDB database access.
"""

import json
import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Force UTF-8 encoding for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables from backend/.env
from dotenv import load_dotenv
load_dotenv(dotenv_path=BACKEND_DIR / ".env", override=True)

from app.agent.tools import classify_error
from app.services.gemini_config import configure_gemini
from app.services.llm_client import generate_text
from app.services.embedding_service import get_embedding
from app.services.vector_store_service import collection


def run_preflight() -> bool:
    """
    Executes preflight diagnostic checks and returns True if all checks pass.
    """
    print("=" * 80)
    print(" EchoInsight System Preflight Diagnostic Harness")
    print("=" * 80)

    all_passed = True

    # -------------------------------------------------------------------------
    # Check 1: GEMINI_API_KEY environment variable
    # -------------------------------------------------------------------------
    print("\n[Check 1/5] GEMINI_API_KEY Environment Variable...")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        try:
            configure_gemini()
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
        except Exception:
            pass

    if api_key:
        print("  --> PASS | GEMINI_API_KEY is set (key hidden for security).")
    else:
        all_passed = False
        err_msg = "GEMINI_API_KEY is missing or empty in backend/.env."
        info = classify_error(err_msg)
        print("  --> FAIL | GEMINI_API_KEY is missing or empty.")
        print(f"      error_type: {info['error_type']} | retry_after_seconds: {info['retry_after_seconds']}")
        print(f"      Details: {err_msg}")

    # Temporarily force LLM_CACHE off for live API checks
    orig_cache = os.environ.get("LLM_CACHE")
    os.environ["LLM_CACHE"] = "0"

    # -------------------------------------------------------------------------
    # Check 2: Live LLM Text Generation with GEMINI_MODEL
    # -------------------------------------------------------------------------
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"
    print(f"\n[Check 2/5] Live LLM Text Generation (Model: {model_name})...")
    try:
        res = generate_text("Reply with the single word OK", json_mode=False)
        if res and len(res.strip()) > 0:
            print(f"  --> PASS | Model '{model_name}' returned valid text response: '{res.strip()}'")
        else:
            raise ValueError("generate_text returned an empty text string.")
    except Exception as e:
        all_passed = False
        err_msg = str(e)
        info = classify_error(err_msg)
        print(f"  --> FAIL | Live text generation failed with model '{model_name}'.")
        print(f"      error_type: {info['error_type']} | retry_after_seconds: {info['retry_after_seconds']}")
        print(f"      Details: {err_msg}")
        if info.get("error_type") == "quota_exhausted":
            print("\n[QUOTA EXHAUSTED] Halting preflight checks immediately due to LLM quota exhaustion. Do not retry.")
            _restore_cache(orig_cache)
            _print_overall(False)
            return False

    # -------------------------------------------------------------------------
    # Check 3: Live LLM JSON Mode Generation
    # -------------------------------------------------------------------------
    print("\n[Check 3/5] Live LLM JSON Mode Generation...")
    try:
        prompt = (
            'Return a JSON object with action equal to "finish" '
            'and final_answer equal to "Preflight check completed successfully."'
        )
        res_json_str = generate_text(prompt, json_mode=True)
        parsed = json.loads(res_json_str)

        if isinstance(parsed, dict) and parsed.get("action") == "finish" and "final_answer" in parsed:
            print(f"  --> PASS | JSON mode returned valid expected schema: {json.dumps(parsed)}")
        else:
            raise ValueError(
                f"JSON schema mismatch. Expected action='finish' and 'final_answer' key. Received: {parsed}"
            )
    except Exception as e:
        all_passed = False
        err_msg = str(e)
        info = classify_error(err_msg)
        print("  --> FAIL | Live JSON mode generation failed.")
        print(f"      error_type: {info['error_type']} | retry_after_seconds: {info['retry_after_seconds']}")
        print(f"      Details: {err_msg}")
        if info.get("error_type") == "quota_exhausted":
            print("\n[QUOTA EXHAUSTED] Halting preflight checks immediately due to LLM quota exhaustion. Do not retry.")
            _restore_cache(orig_cache)
            _print_overall(False)
            return False

    # -------------------------------------------------------------------------
    # Check 4: Live Text Embedding Vector Generation
    # -------------------------------------------------------------------------
    print("\n[Check 4/5] Live Text Embedding Generation...")
    try:
        vector = get_embedding("EchoInsight preflight diagnostic test string")
        if vector and isinstance(vector, list) and len(vector) > 0:
            print(f"  --> PASS | get_embedding returned valid vector with length {len(vector)} dimensions.")
        else:
            raise ValueError("get_embedding returned an empty vector or non-list object.")
    except Exception as e:
        all_passed = False
        err_msg = str(e)
        info = classify_error(err_msg)
        print("  --> FAIL | Text embedding generation failed.")
        print(f"      error_type: {info['error_type']} | retry_after_seconds: {info['retry_after_seconds']}")
        print(f"      Details: {err_msg}")
        if info.get("error_type") == "quota_exhausted":
            print("\n[QUOTA EXHAUSTED] Halting preflight checks immediately due to LLM quota exhaustion. Do not retry.")
            _restore_cache(orig_cache)
            _print_overall(False)
            return False

    # Restore original LLM_CACHE env var setting
    _restore_cache(orig_cache)

    # -------------------------------------------------------------------------
    # Check 5: ChromaDB Collection Access & Item Count
    # -------------------------------------------------------------------------
    print("\n[Check 5/5] ChromaDB Collection Access & Item Count...")
    try:
        item_count = collection.count()
        print(f"  --> PASS | ChromaDB collection 'feedback_memory' opened. Item count: {item_count}")
    except Exception as e:
        all_passed = False
        err_msg = str(e)
        info = classify_error(err_msg)
        print("  --> FAIL | ChromaDB collection access failed.")
        print(f"      error_type: {info['error_type']} | retry_after_seconds: {info['retry_after_seconds']}")
        print(f"      Details: {err_msg}")

    # -------------------------------------------------------------------------
    # Overall Preflight Result
    # -------------------------------------------------------------------------
    _print_overall(all_passed)
    return all_passed


def _restore_cache(orig_cache: str | None) -> None:
    if orig_cache is not None:
        os.environ["LLM_CACHE"] = orig_cache
    else:
        os.environ.pop("LLM_CACHE", None)


def _print_overall(all_passed: bool) -> None:
    print("\n" + "=" * 80)
    if all_passed:
        print(" PREFLIGHT SYSTEM VERIFICATION SUMMARY: PASS")
    else:
        print(" PREFLIGHT SYSTEM VERIFICATION SUMMARY: FAIL")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    success = run_preflight()
    sys.exit(0 if success else 1)
