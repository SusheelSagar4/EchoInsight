"""
backend/app/services/embedding_service.py

Service for generating text embeddings using Google's Gemini API.

==============================================================================
WHAT IS AN EMBEDDING? (FOR BEGINNERS)
==============================================================================
Imagine you want a computer to understand the meaning of human words or sentences. 
Computers don't naturally understand concepts like "happy", "bug report", or 
"login issue", but they are exceptionally good at working with numbers.

An EMBEDDING is a technique that converts a piece of text (like a sentence or 
customer feedback item) into a long list of numbers called a "vector" 
(for example: [0.0123, -0.0456, 0.8912, ...]).

Why is this useful?
1. Semantic Meaning: Texts with similar meanings get numbers that are close to
   each other in mathematical space. For example, "The app crashed on login" and
   "Cannot sign in after launching the app" will produce very similar embedding vectors!
2. Search & Clustering: By comparing these lists of numbers using geometry/distance,
   we can easily search for related customer feedback in a vector database (like ChromaDB)
   or group similar user complaints together automatically.
==============================================================================
"""

import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# ==============================================================================
# Step 1: Explicitly Locate and Load backend/.env File
# ==============================================================================
# Find the exact path to backend/.env relative to this file's location:
# embedding_service.py -> app/services/ -> app/ -> backend/ -> .env
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)


def configure_gemini() -> str:
    """
    Helper function to get and configure the Gemini API key from backend/.env.
    Reuses the exact same configuration pattern as clustering_service.py.
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


# ==============================================================================
# Step 2: Get Text Embedding Function
# ==============================================================================
def get_embedding(text: str) -> list[float]:
    """
    Generates a numerical embedding vector for the provided text using Gemini's
    text-embedding-004 model.

    What this function does:
    1. Validates that the input text is non-empty.
    2. Configures the Gemini API using the API key loaded from backend/.env.
    3. Calls genai.embed_content() with model="models/text-embedding-004" and
       task_type="retrieval_document".
    4. Extracts and returns the resulting vector (list of floats).
    5. Wraps execution in a try/except block to raise clear errors if something fails.

    Args:
        text (str): The input text string to convert into an embedding vector.

    Returns:
        list[float]: A list of floating-point numbers representing the text's
                     semantic embedding vector.

    Raises:
        ValueError: If input text is invalid, API key is missing, or embedding fails.
    """
    if not text or not isinstance(text, str) or not text.strip():
        raise ValueError("Input text for get_embedding must be a non-empty string.")

    # Ensure Gemini SDK is configured with the API key
    configure_gemini()

    try:
        # Call Gemini's embedding API endpoint
        # Attempts model="models/text-embedding-004" first as requested, falling back to
        # model="models/gemini-embedding-001" if text-embedding-004 is unavailable in API v1beta.
        try:
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=text.strip(),
                task_type="retrieval_document"
            )
        except Exception as primary_err:
            if "404" in str(primary_err) or "not found" in str(primary_err).lower():
                response = genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=text.strip(),
                    task_type="retrieval_document"
                )
            else:
                raise primary_err

        # Extract the vector list of floats from the response dictionary
        embedding_vector = response.get("embedding")

        if not embedding_vector:
            raise ValueError("Gemini API returned an empty embedding response.")

        return embedding_vector

    except Exception as e:
        # Wrap any network, authorization, or model failure in a clear ValueError
        raise ValueError(f"Failed to generate embedding with Gemini API: {str(e)}")
