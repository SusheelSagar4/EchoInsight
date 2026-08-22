import csv
import io
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from ..models import FeedbackCluster, PRD
from ..services.clustering_service import cluster_feedback
from ..services.prd_service import generate_prd

# ==============================================================================
# Create FastAPI Router
# ==============================================================================
# Create an APIRouter instance with a common path prefix `/feedback` and tag `feedback` for API documentation
router = APIRouter(prefix="/feedback", tags=["feedback"])


# ==============================================================================
# Request Body Model for Clustering
# ==============================================================================
class ClusterRequest(BaseModel):
    """
    Schema for incoming raw feedback payload sent by the frontend client.
    """
    raw_feedback: str


# ==============================================================================
# Endpoint 1: POST /feedback/cluster
# ==============================================================================
# What it does: Accepts a string of raw customer feedback, invokes Gemini AI to tag sentiment/intent,
# groups items into thematic clusters, calculates RICE scores, and returns a list of FeedbackCluster objects.
# When the frontend calls it: When a user pastes raw customer reviews/tickets and clicks "Analyze & Cluster".
@router.post(
    "/cluster",
    response_model=list[FeedbackCluster],
    summary="Cluster raw customer feedback using Gemini AI"
)
def cluster_feedback_endpoint(request: ClusterRequest) -> list[FeedbackCluster]:
    """
    Endpoint to process raw feedback text and return structured thematic clusters with RICE scores.
    """
    try:
        clusters = cluster_feedback(request.raw_feedback)
        return clusters
    except Exception as e:
        # Return HTTP 500 error code with descriptive message if AI processing fails
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cluster feedback: {str(e)}"
        )


# ==============================================================================
# Endpoint 2: POST /feedback/cluster-csv
# ==============================================================================
# What it does: Accepts an uploaded CSV file containing feedback items in the first column,
# parses lines, joins them, and invokes Gemini AI clustering.
# When the frontend calls it: When a user uploads a .csv file of customer feedback.
@router.post(
    "/cluster-csv",
    response_model=list[FeedbackCluster],
    summary="Cluster customer feedback uploaded via a CSV file"
)
async def cluster_csv_endpoint(file: UploadFile = File(...)) -> list[FeedbackCluster]:
    """
    Endpoint to process an uploaded CSV file, extract feedback text from column 1,
    and return structured thematic clusters with RICE scores.
    """
    # 1. Parse uploaded CSV file contents
    try:
        # Read the binary data stream uploaded by the client
        contents = await file.read()

        # Decode binary bytes into a standard UTF-8 text string (utf-8-sig strips potential byte-order marks)
        decoded_content = contents.decode("utf-8-sig")

        # io.StringIO converts the string into an in-memory file stream so csv.reader can iterate over it
        string_io = io.StringIO(decoded_content)

        # Create Python's standard CSV reader object
        reader = csv.reader(string_io)

        extracted_lines = []

        # Iterate over each row parsed from the CSV file
        for row in reader:
            # Skip empty rows or rows where the first cell has no content
            if not row or not row[0].strip():
                continue

            first_cell_text = row[0].strip()

            # Check if this is the very first line and looks like a header label (e.g. "feedback", "text", "comments")
            if len(extracted_lines) == 0 and first_cell_text.lower() in [
                "feedback", "text", "comment", "comments", "review", "reviews", "raw_feedback", "customer feedback"
            ]:
                # Skip header row
                continue

            # Add valid feedback text to our list of extracted feedback lines
            extracted_lines.append(first_cell_text)

        # Validate that we found at least one non-empty feedback item
        if not extracted_lines:
            raise HTTPException(
                status_code=400,
                detail="CSV file must contain at least one valid feedback entry in the first column."
            )

        # Join all extracted feedback items into a single string with newlines separating each line
        joined_feedback_string = "\n".join(extracted_lines)

    except HTTPException:
        # Re-raise explicit HTTP exceptions (e.g. validation 400 error)
        raise
    except Exception as e:
        # Catch any unexpected CSV parsing/decoding errors and return a 400 Bad Request status code
        raise HTTPException(
            status_code=400,
            detail=f"Invalid CSV file format: {str(e)}"
        )

    # 2. Invoke clustering logic on joined feedback text
    try:
        clusters = cluster_feedback(joined_feedback_string)
        return clusters
    except Exception as e:
        # Catch clustering process errors and return a 500 Internal Server Error status code
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cluster feedback from CSV: {str(e)}"
        )


# ==============================================================================
# Endpoint 3: POST /feedback/prd
# ==============================================================================
# What it does: Accepts a single FeedbackCluster object and passes it to Gemini AI to generate
# a complete Product Requirements Document (PRD) containing user stories, acceptance criteria, and KPIs.
# When the frontend calls it: When a product manager clicks "Generate PRD" on a specific feedback cluster.
@router.post(
    "/prd",
    response_model=PRD,
    summary="Generate a PRD from a prioritized feedback cluster"
)
def generate_prd_endpoint(cluster: FeedbackCluster) -> PRD:
    """
    Endpoint to draft an AI-generated Product Requirements Document (PRD) for a selected cluster.
    """
    try:
        prd = generate_prd(cluster)
        return prd
    except Exception as e:
        # Return HTTP 500 error code with descriptive message if PRD generation fails
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PRD: {str(e)}"
        )

