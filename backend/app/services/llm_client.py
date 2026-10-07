"""
backend/app/services/llm_client.py

Unified LLM Client Service for Google Gemini API with model configuration
and optional local development response caching.

==============================================================================
WHAT IS THIS SERVICE FOR? (FOR BEGINNERS)
==============================================================================
Instead of hardcoding Gemini model names or making direct API calls across
multiple files, this client centralizes LLM calls into a single helper:
`generate_text(prompt, json_mode)`.

Features:
1. Dynamic Model Selection: Reads `GEMINI_MODEL` env var (default: "gemini-3.6-flash").
2. Local Dev Caching: If `LLM_CACHE=1`, caches responses in `backend/data/llm_cache/`
   keyed by SHA-256 prompt hash. Reuses stored responses during local dev/testing
   to prevent rate-limit errors and save API quota.
==============================================================================
"""

import hashlib
import json
import os
from pathlib import Path

import google.generativeai as genai
from .gemini_config import configure_gemini

# Resolve path to backend/data/llm_cache directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
CACHE_DIR = DATA_DIR / "llm_cache"


def generate_text(prompt: str, json_mode: bool = False) -> str:
    """
    Generates text output from Gemini LLM for the given prompt string.

    Args:
        prompt (str): Prompt text to send to Gemini LLM.
        json_mode (bool): If True, requests JSON output structure from Gemini.

    Returns:
        str: Raw text string returned by the model.
    """
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt for generate_text must be a non-empty string.")

    # Configure Gemini API credentials
    configure_gemini()

    # Read model name from env var (default: gemini-3.6-flash)
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash"

    # Check if dev caching is enabled via LLM_CACHE=1
    cache_enabled = os.getenv("LLM_CACHE", "0").strip() in ["1", "true", "TRUE", "True"]

    # Generate unique hash key for prompt and parameters
    cache_key_str = f"{model_name}:{json_mode}:{prompt.strip()}"
    cache_hash = hashlib.sha256(cache_key_str.encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"{cache_hash}.json"

    # 1. Check local dev cache if enabled
    if cache_enabled and cache_file.exists():
        try:
            with open(cache_file, mode="r", encoding="utf-8") as f:
                cached_data = json.load(f)
                response_text = cached_data.get("response_text")
                if response_text:
                    print(f"[cache hit] Reusing cached LLM response for hash {cache_hash[:10]}")
                    return response_text
        except Exception as cache_err:
            print(f"[cache warning] Failed to read cache file {cache_file.name}: {cache_err}")

    # 2. Live API Call
    if cache_enabled:
        print(f"[live call] Fetching live LLM response from {model_name} for hash {cache_hash[:10]}")

    model = genai.GenerativeModel(model_name)
    gen_config = {"response_mime_type": "application/json"} if json_mode else None

    response = model.generate_content(
        prompt,
        generation_config=gen_config
    )

    raw_text = response.text.strip()

    # 3. Save to local dev cache if enabled
    if cache_enabled:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_payload = {
                "model": model_name,
                "json_mode": json_mode,
                "prompt": prompt,
                "response_text": raw_text
            }
            with open(cache_file, mode="w", encoding="utf-8") as f:
                json.dump(cache_payload, f, indent=2)
        except Exception as write_err:
            print(f"[cache warning] Failed to write cache file {cache_file.name}: {write_err}")

    return raw_text
