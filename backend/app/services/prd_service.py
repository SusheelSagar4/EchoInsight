import json
import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from ..models import PRD, FeedbackCluster

# ==============================================================================
# Step 1: Explicitly Locate and Load backend/.env File
# ==============================================================================
# Find the exact path to backend/.env relative to this file's location
# prd_service.py -> app/services/ -> app/ -> backend/ -> .env
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)


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
# Step 2: Main PRD Generation Function
# ==============================================================================
def generate_prd(cluster: FeedbackCluster) -> PRD:
    """
    Takes a FeedbackCluster object, passes its feedback items and RICE metrics to Gemini AI,
    and returns an automatically drafted Product Requirements Document (PRD) Pydantic object.
    """
    # Configure Gemini SDK with the loaded API key
    configure_gemini()

    # ==========================================================================
    # Step 3: Format Feedback Items & RICE Context for the AI Prompt
    # ==========================================================================
    feedback_summary = "\n".join(
        [
            f"- [{item.sentiment} | {item.intent} | Urgency: {item.urgency}] \"{item.text}\""
            for item in cluster.feedback_items
        ]
    )

    # ==========================================================================
    # Step 4: Construct the AI Prompt
    # ==========================================================================
    prompt = f"""
    You are a Senior Product Manager. Draft a comprehensive Product Requirements Document (PRD) for the following prioritized feedback cluster:

    --- CLUSTER DETAILS ---
    Theme Name: {cluster.theme_name}
    RICE Score: {cluster.rice_score:.2f} (Reach: {cluster.reach}%, Impact: {cluster.impact}, Confidence: {cluster.confidence}, Effort: {cluster.effort} person-weeks)
    Feedback Count: {cluster.frequency} items

    --- USER FEEDBACK QUOTES ---
    {feedback_summary}
    ------------------------

    Perform the following tasks:
    1. title: Create a clear, professional feature/initiative title.
    2. problem_statement: Write a 2-3 sentence problem statement grounded directly in the user feedback quotes and theme.
    3. user_stories: Provide 3-5 user stories formatted strictly as "As a [user type], I want [goal] so that [benefit]".
    4. acceptance_criteria: Provide 4-6 clear, testable acceptance criteria bullet points.
    5. kpis: Provide 3-4 measurable key performance indicators (KPIs) to measure feature success post-launch.

    CRITICAL OUTPUT REQUIREMENTS:
    - Output ONLY valid, raw JSON without markdown formatting, code fences (no ```json), or explanatory text.
    - The JSON object must match this exact schema:
    {{
      "title": "Feature Title Here",
      "problem_statement": "2-3 sentence description of the user pain point...",
      "user_stories": [
        "As a user, I want ... so that ..."
      ],
      "acceptance_criteria": [
        "System must ..."
      ],
      "kpis": [
        "Increase metric X by Y% ..."
      ]
    }}
    """

    # ==========================================================================
    # Step 5: Call Gemini API & Parse Output
    # ==========================================================================
    try:
        # Initialize Gemini 3.6 Flash model
        model = genai.GenerativeModel("gemini-3.6-flash")

        # Request JSON output from Gemini
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        # Extract response text
        raw_text = response.text.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()

        # Parse JSON string into Python dict
        parsed_data = json.loads(raw_text)

        # Construct and return the PRD object, linking the originating cluster
        prd = PRD(
            title=parsed_data["title"],
            problem_statement=parsed_data["problem_statement"],
            user_stories=parsed_data["user_stories"],
            acceptance_criteria=parsed_data["acceptance_criteria"],
            kpis=parsed_data["kpis"],
            linked_cluster=cluster
        )

        return prd

    except Exception as e:
        # Catch any network, parsing, or key error and raise a clear ValueError
        raise ValueError(f"Failed to generate PRD with Gemini: {str(e)}")
