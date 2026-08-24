import json
import os
from pathlib import Path
import uuid
import google.generativeai as genai
from dotenv import load_dotenv

from ..models import FeedbackCluster, FeedbackItem
from .embedding_service import get_embedding
from .vector_store_service import find_similar_feedback, store_feedback_item

# ==============================================================================
# Step 1: Explicitly Locate and Load backend/.env File
# ==============================================================================
# Find the exact path to backend/.env relative to this file's location
# clustering_service.py -> app/services/ -> app/ -> backend/ -> .env
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)


# Helper function to get and configure the Gemini API key
def configure_gemini():
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
# Step 2: Main Clustering Function
# ==============================================================================
def cluster_feedback(raw_feedback: str) -> list[FeedbackCluster]:
    """
    Takes raw customer feedback text (one item per line), sends it to Gemini AI for
    sentiment tagging, thematic grouping, and RICE prioritization scoring, enriches
    items with past vector similarity counts, stores items in long-term memory (ChromaDB),
    and returns a list of structured FeedbackCluster objects.
    """
    # Configure Gemini SDK with the loaded API key
    configure_gemini()

    # Validate input is not empty
    if not raw_feedback or not raw_feedback.strip():
        return []

    # ==========================================================================
    # Step 3: Construct the AI Prompt
    # ==========================================================================
    prompt = f"""
    You are an expert Product Manager and AI Data Analyst. Analyze the following raw customer feedback:

    --- RAW FEEDBACK ---
    {raw_feedback}
    --------------------

    Perform the following tasks:
    1. Tag each individual feedback line with:
       - sentiment: Exactly one of "Positive", "Negative", or "Neutral"
       - intent: Exactly one of "Bug", "Feature Request", or "UX Friction"
       - urgency: Exactly one of "Low", "Medium", or "High"
    
    2. Group similar feedback items into thematic clusters based on their underlying topic.
    
    3. For each thematic cluster, estimate the following RICE prioritization metrics:
       - frequency: Integer count of feedback items in this cluster
       - reach: Float between 0 and 100 representing the percentage of total users affected
       - impact: Float between 1.0 and 3.0 (1.0 = Low, 2.0 = Medium, 3.0 = High impact)
       - confidence: Float between 0.0 and 1.0 (e.g., 0.8 = 80% confidence)
       - effort: Float in person-weeks required to build/fix (e.g., 0.5 to 8.0)
       - rice_score: Calculate as (reach * impact * confidence) / effort
    
    CRITICAL OUTPUT REQUIREMENTS:
    - Output ONLY valid, raw JSON without markdown formatting, code fences (no ```json), or explanatory text.
    - The output must be a JSON array of objects matching this exact structure:
    [
      {{
        "theme_name": "Cluster Name Here",
        "feedback_items": [
          {{
            "text": "Exact or cleaned feedback text",
            "sentiment": "Positive",
            "intent": "Feature Request",
            "urgency": "Low"
          }}
        ],
        "frequency": 1,
        "reach": 25.0,
        "impact": 2.0,
        "confidence": 0.8,
        "effort": 1.0,
        "rice_score": 40.0
      }}
    ]
    """

    # ==========================================================================
    # Step 4: Call Gemini API & Parse Output
    # ==========================================================================
    try:
        # Initialize Gemini 3.6 Flash model (fast, accurate, and free-tier friendly)
        model = genai.GenerativeModel("gemini-3.6-flash")

        # Request JSON output from Gemini model
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        # Extract response text
        raw_text = response.text.strip()

        # Clean potential markdown code fences if present in response
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()

        # Parse JSON string into Python list/dict structures
        parsed_json = json.loads(raw_text)

        # Ensure the parsed response is a list
        if not isinstance(parsed_json, list):
            raise ValueError("Gemini response is not a valid JSON array of clusters.")

        # Convert raw dictionaries into validated Pydantic FeedbackCluster objects
        clusters = [FeedbackCluster(**item) for item in parsed_json]

        # ==========================================================================
        # Step 5: Long-Term Vector Memory & Similarity Search Enrichment
        # ==========================================================================
        # This section checks ChromaDB for past feedback similar to each item in the
        # current cluster, sets similar_past_count, and stores the new items for future calls.
        # Wrapped in try/except so vector memory failures log a warning without crashing clustering.
        try:
            for cluster in clusters:
                for item in cluster.feedback_items:
                    # a. Generate an embedding vector for the feedback item's text
                    item_embedding = get_embedding(item.text)

                    # b. Query ChromaDB for top 5 most similar past feedback items
                    past_matches = find_similar_feedback(embedding=item_embedding, top_k=5)

                    # c. Count matches with a similarity distance below 0.3
                    # Plain-English explanation: Distance measures how different two vectors are.
                    # A distance closer to 0 means higher similarity. We consider distance < 0.3
                    # as a "meaningful semantic match".
                    # NOTE: This threshold value (0.3) can be adjusted/tuned based on real-world results.
                    similar_count = sum(
                        1 for match in past_matches if match.get("distance", 1.0) < 0.3
                    )

                    # d. Set the feedback item's similar_past_count field
                    item.similar_past_count = similar_count

                    # e. Generate a unique ID for this feedback item using UUID v4
                    item_id = str(uuid.uuid4())

                    # f. Store this feedback item and its embedding into ChromaDB memory
                    store_feedback_item(
                        item_id=item_id,
                        text=item.text,
                        embedding=item_embedding,
                        theme_name=cluster.theme_name,
                        sentiment=item.sentiment,
                        intent=item.intent,
                        urgency=item.urgency
                    )
        except Exception as vector_err:
            # Log a warning message if vector memory search/storage fails, allowing clustering to succeed
            print(f"Warning: Vector memory search or storage failed: {str(vector_err)}")

        return clusters

    except Exception as e:
        # Catch any API network, parsing, or Pydantic validation errors and raise a clear ValueError
        raise ValueError(f"Failed to process and cluster feedback with Gemini: {str(e)}")

