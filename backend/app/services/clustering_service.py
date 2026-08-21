import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
from ..models import FeedbackCluster, FeedbackItem

# ==============================================================================
# Step 1: Load Environment Variables
# ==============================================================================
# Read the .env file to load secret keys like GEMINI_API_KEY into system environment
load_dotenv()

# Retrieve the API key from environment variables
api_key = os.environ.get("GEMINI_API_KEY")

# Configure the Google Generative AI SDK with the retrieved API key if available
if api_key:
    genai.configure(api_key=api_key)


# ==============================================================================
# Step 2: Main Clustering Function
# ==============================================================================
def cluster_feedback(raw_feedback: str) -> list[FeedbackCluster]:
    """
    Takes raw customer feedback text (one item per line), sends it to Gemini AI for
    sentiment tagging, thematic grouping, and RICE prioritization scoring, and returns
    a list of structured FeedbackCluster objects.
    """
    # Check if API key is configured before calling Gemini
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Please set it in your backend/.env file."
        )

    # Validate input is not empty
    if not raw_feedback or not raw_feedback.strip():
        return []

    # ==========================================================================
    # Step 3: Construct the AI Prompt
    # ==========================================================================
    # We craft a detailed prompt telling Gemini exactly how to categorize,
    # group, score, and format the output as strict JSON.
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
        # Initialize Gemini 2.0 Flash model (fast, accurate, and free-tier friendly)
        model = genai.GenerativeModel("gemini-2.0-flash")

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

        return clusters

    except Exception as e:
        # Catch any API network, parsing, or Pydantic validation errors and raise a clear ValueError
        raise ValueError(f"Failed to process and cluster feedback with Gemini: {str(e)}")
