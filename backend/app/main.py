"""
backend/app/main.py

Entry point for the EchoInsight FastAPI backend application.
Configures app metadata, CORS middleware, includes API routers,
and handles root sanity check endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.feedback import router as feedback_router

# Create main FastAPI application instance with explicit docs and openapi configuration
app = FastAPI(
    title="EchoInsight API",
    description="Autonomous Customer Feedback-to-PRD Pipeline",
    version="1.1",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url="/redoc"
)

# Add CORS middleware allowing all origins for local development (frontend runs on different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the feedback router (/feedback/cluster and /feedback/prd)
app.include_router(feedback_router)


# Root sanity check endpoint
@app.get("/")
def read_root():
    return {"status": "EchoInsight API is running"}
