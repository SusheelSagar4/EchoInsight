"""
backend/app/services/gemini_config.py

Shared configuration helper for locating backend/.env and initializing the Google Gemini AI SDK.
"""

import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Resolve exact path to backend/.env relative to this file's location
# gemini_config.py -> app/services/ -> app/ -> backend/ -> .env
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def configure_gemini() -> str:
    """
    Loads environment variables from backend/.env and configures the Google Generative AI SDK
    with the GEMINI_API_KEY.

    Returns:
        str: The configured Gemini API key.

    Raises:
        ValueError: If GEMINI_API_KEY is missing or empty in backend/.env.
    """
    # Reload environment to ensure latest key from backend/.env is active
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise ValueError(
            f"GEMINI_API_KEY is missing or empty in {ENV_PATH}. Please add a valid Gemini API key to backend/.env."
        )

    # Configure google-generativeai SDK explicitly before any model call
    genai.configure(api_key=api_key)
    return api_key
