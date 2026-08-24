from typing import Literal
from pydantic import BaseModel


class FeedbackItem(BaseModel):
    """
    Represents an individual piece of customer feedback, tagged with key metadata
    including sentiment classification, underlying user intent, and urgency level.
    """

    text: str
    sentiment: Literal["Positive", "Negative", "Neutral"]
    intent: Literal["Bug", "Feature Request", "UX Friction"]
    urgency: Literal["Low", "Medium", "High"]
    similar_past_count: int = 0  # Represents how many similar past feedback items were found for this item



class FeedbackCluster(BaseModel):
    """
    Represents a aggregated group of related feedback items sharing a common theme,
    along with calculated RICE framework metrics (Reach, Impact, Confidence, Effort, RICE Score) for prioritization.
    """

    theme_name: str
    feedback_items: list[FeedbackItem]
    frequency: int
    reach: float
    impact: float
    confidence: float
    effort: float
    rice_score: float


class PRD(BaseModel):
    """
    Represents a Product Requirements Document (PRD) generated for a prioritized feature or bug,
    containing user stories, acceptance criteria, target KPIs, and a link to the originating feedback cluster.
    """

    title: str
    problem_statement: str
    user_stories: list[str]
    acceptance_criteria: list[str]
    kpis: list[str]
    linked_cluster: FeedbackCluster
