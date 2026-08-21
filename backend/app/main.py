from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import feedback

# Create main FastAPI application instance
app = FastAPI(
    title="EchoInsight API",
    description="AI-powered customer feedback clustering and automated PRD generation API",
    version="1.0.0"
)

# Enable CORS (Cross-Origin Resource Sharing) so the React frontend can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the feedback router (/feedback/cluster and /feedback/prd)
app.include_router(feedback.router)


@app.get("/", summary="API Health Check")
def read_root():
    return {
        "status": "healthy",
        "service": "EchoInsight API",
        "version": "1.0.0"
    }
