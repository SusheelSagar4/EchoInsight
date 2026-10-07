"""
backend/app/routers/agent.py

FastAPI Router for EchoInsight Autonomous Agent execution & lifecycle management.

==============================================================================
WHAT IS THIS ROUTER FOR? (FOR BEGINNERS)
==============================================================================
This module exposes REST endpoints to allow external clients (web apps, frontends,
integrations) to start, monitor, approve, and manage agent runs asynchronously.

Endpoints:
- POST /agent/run: Accepts a goal and launches an agent loop in a background thread.
- GET /agent/runs/{run_id}: Retrieves live execution status, event trace, and pending approval.
- POST /agent/runs/{run_id}/approve: Resumes a paused run with human approval/rejection.
==============================================================================
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.agent.loop import RUNS_DIR, ApprovalTimeoutError, run_agent
from app.agent.planner import GeminiPlanner, ScriptedPlanner

router = APIRouter(prefix="/agent", tags=["Agent"])


# ==============================================================================
# In-Memory Thread-Safe Run State Container
# ==============================================================================
@dataclass
class AgentRunState:
    """Stores active run execution state in memory for real-time querying & approval."""
    run_id: str
    goal: str
    status: str = "running"
    pending_approval: Optional[Dict[str, Any]] = None
    final_answer: Optional[str] = None
    trace: List[Dict[str, Any]] = field(default_factory=list)
    approval_event: threading.Event = field(default_factory=threading.Event)
    approval_decision: Optional[bool] = None
    approval_timeout_seconds: float = 600.0  # 10 minutes default approval timeout
    lock: threading.Lock = field(default_factory=threading.Lock)


# Thread-safe global run store
RUN_STORE_LOCK = threading.Lock()
RUN_STORE: Dict[str, AgentRunState] = {}


# ==============================================================================
# Request and Response Schemas
# ==============================================================================
class RunRequest(BaseModel):
    goal: str = Field(..., description="The natural language objective for the agent")
    scripted_file: Optional[str] = Field(None, description="Path to optional JSON scripted decisions file for offline testing/demos")
    decisions: Optional[List[Dict[str, Any]]] = Field(None, description="Optional inline list of scripted decisions for testing")
    approval_timeout_seconds: Optional[float] = Field(600.0, description="Timeout duration in seconds for approval pauses (default: 600s / 10m)")
    max_steps: Optional[int] = Field(10, description="Maximum execution step cap")


class RunResponse(BaseModel):
    run_id: str
    status: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    pending_approval: Optional[Dict[str, Any]] = None
    final_answer: Optional[str] = None
    trace: List[Dict[str, Any]]


class ApproveRequest(BaseModel):
    approved: bool = Field(..., description="True to approve execution, False to reject")


class ApproveResponse(BaseModel):
    run_id: str
    status: str
    approved: bool


# ==============================================================================
# Endpoint 1: POST /agent/run
# ==============================================================================
@router.post("/run", response_model=RunResponse)
def start_agent_run(payload: RunRequest):
    """
    Starts an agent execution run in a background worker thread.
    Returns immediately with {run_id, status}.
    """
    run_id = f"run_{uuid.uuid4().hex[:10]}"

    # Select Planner (ScriptedPlanner if decisions/scripted_file provided, else GeminiPlanner)
    if payload.decisions is not None:
        planner = ScriptedPlanner(payload.decisions)
    elif payload.scripted_file:
        s_path = Path(payload.scripted_file)
        if not s_path.exists():
            raise HTTPException(status_code=400, detail=f"Scripted decision file not found at {payload.scripted_file}")
        try:
            with open(s_path, mode="r", encoding="utf-8") as f:
                decisions = json.load(f)
            planner = ScriptedPlanner(decisions)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to load scripted decisions JSON: {str(e)}")
    else:
        planner = GeminiPlanner()

    timeout_sec = payload.approval_timeout_seconds if payload.approval_timeout_seconds is not None else 600.0

    run_state = AgentRunState(
        run_id=run_id,
        goal=payload.goal,
        status="running",
        approval_timeout_seconds=timeout_sec
    )

    with RUN_STORE_LOCK:
        RUN_STORE[run_id] = run_state

    def event_callback(evt: Dict[str, Any]) -> None:
        """Callback triggered on each event to record trace live in-memory."""
        with run_state.lock:
            run_state.trace.append(evt)

    def api_approval_handler(tool_name: str, args: Dict[str, Any], reason: str) -> bool:
        """
        API Approval Handler: Pauses execution thread, marks state as waiting_approval,
        and blocks on threading.Event until POST /approve is called or timeout expires.
        """
        with run_state.lock:
            run_state.status = "waiting_approval"
            run_state.pending_approval = {
                "tool": tool_name,
                "args": args,
                "reason": reason
            }
            run_state.approval_event.clear()
            run_state.approval_decision = None

        # Wait for user input or timeout (default 10 minutes)
        signaled = run_state.approval_event.wait(timeout=run_state.approval_timeout_seconds)

        with run_state.lock:
            if not signaled:
                run_state.status = "approval_timeout"
                run_state.pending_approval = None
                raise ApprovalTimeoutError("Approval request timed out waiting for human input.")

            decision = run_state.approval_decision
            run_state.pending_approval = None
            run_state.status = "running"
            return bool(decision)

    def _worker():
        try:
            res = run_agent(
                goal=payload.goal,
                planner=planner,
                approval_handler=api_approval_handler,
                max_steps=payload.max_steps or 10,
                event_callback=event_callback,
                run_id=run_id
            )
            with run_state.lock:
                run_state.status = res.get("status", "completed")
                run_state.final_answer = res.get("final_answer")
                run_state.trace = res.get("trace", run_state.trace)
                run_state.pending_approval = None
        except Exception as e:
            with run_state.lock:
                if run_state.status != "approval_timeout":
                    run_state.status = "failed"
                    run_state.final_answer = f"Agent execution error: {str(e)}"
                    run_state.pending_approval = None

    worker_thread = threading.Thread(target=_worker, daemon=True)
    worker_thread.start()

    return RunResponse(run_id=run_id, status="running")


# ==============================================================================
# Endpoint 2: GET /agent/runs/{run_id}
# ==============================================================================
@router.get("/runs/{run_id}", response_model=RunStatusResponse)
def get_run_status(run_id: str):
    """
    Returns current status, trace so far, and pending_approval details if paused for approval.
    """
    with RUN_STORE_LOCK:
        run_state = RUN_STORE.get(run_id)

    if run_state:
        with run_state.lock:
            return RunStatusResponse(
                run_id=run_state.run_id,
                status=run_state.status,
                pending_approval=run_state.pending_approval,
                final_answer=run_state.final_answer,
                trace=list(run_state.trace)
            )

    # Check persistent storage (JSON trace file) if not active in memory store
    file_path = RUNS_DIR / f"{run_id}.json"
    if file_path.exists():
        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                saved_run = json.load(f)
            return RunStatusResponse(
                run_id=saved_run.get("run_id", run_id),
                status=saved_run.get("status", "completed"),
                pending_approval=None,
                final_answer=saved_run.get("final_answer"),
                trace=saved_run.get("trace", [])
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read run trace file: {str(e)}")

    raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")


# ==============================================================================
# Endpoint 3: POST /agent/runs/{run_id}/approve
# ==============================================================================
@router.post("/runs/{run_id}/approve", response_model=ApproveResponse)
def approve_run(run_id: str, payload: ApproveRequest):
    """
    Resumes a paused run waiting for human approval by sending approved=True or approved=False.
    """
    with RUN_STORE_LOCK:
        run_state = RUN_STORE.get(run_id)

    if not run_state:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    with run_state.lock:
        if run_state.status != "waiting_approval" or run_state.pending_approval is None:
            raise HTTPException(
                status_code=400,
                detail=f"Run '{run_id}' is not waiting for approval (current status: '{run_state.status}')."
            )

        run_state.approval_decision = payload.approved
        run_state.approval_event.set()

    return ApproveResponse(
        run_id=run_id,
        status="resuming",
        approved=payload.approved
    )
