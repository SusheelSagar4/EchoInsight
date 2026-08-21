from fastapi import APIRouter, HTTPException
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
# Endpoint 2: POST /feedback/prd
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
