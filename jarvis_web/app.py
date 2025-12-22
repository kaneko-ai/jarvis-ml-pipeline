"""FastAPI Web Application.

Per RP-167, provides HTTP API for JARVIS.
"""
from __future__ import annotations

import os
from typing import Optional
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException, Depends, Header
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    HTTPException = None
    BaseModel = object


# Create app if FastAPI available
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="JARVIS Research OS",
        description="API for paper survey and knowledge synthesis",
        version="4.2.0",
    )
else:
    app = None


# Request/Response models
class RunRequest(BaseModel):
    """Request to start a run."""

    query: str
    max_papers: int = 10
    seed: int = 42
    config: dict = {}


class RunResponse(BaseModel):
    """Response from a run."""

    run_id: str
    status: str
    message: str


class ShowRunResponse(BaseModel):
    """Response with run details."""

    run_id: str
    status: str
    created_at: str
    query: str
    claims_count: int
    papers_count: int


# Authentication (RP-168)
def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify authorization token."""
    expected = os.environ.get("JARVIS_WEB_TOKEN", "")
    if not expected:
        return True  # No auth required

    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.replace("Bearer ", "")
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")

    return True


if FASTAPI_AVAILABLE:

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

    @app.post("/run", response_model=RunResponse)
    async def start_run(request: RunRequest, _: bool = Depends(verify_token)):
        """Start a new paper survey run."""
        import uuid

        run_id = str(uuid.uuid4())

        # TODO: Actual run execution via jarvis_core
        # For now, return placeholder

        return RunResponse(
            run_id=run_id,
            status="queued",
            message=f"Run queued for query: {request.query}",
        )

    @app.get("/run/{run_id}", response_model=ShowRunResponse)
    async def show_run(run_id: str, _: bool = Depends(verify_token)):
        """Get run details."""
        from pathlib import Path

        run_path = Path("data/runs") / run_id

        if not run_path.exists():
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

        # Load run summary
        summary_path = run_path / "summary.json"
        if summary_path.exists():
            import json

            with open(summary_path) as f:
                summary = json.load(f)
        else:
            summary = {}

        return ShowRunResponse(
            run_id=run_id,
            status=summary.get("status", "unknown"),
            created_at=summary.get("created_at", ""),
            query=summary.get("query", ""),
            claims_count=summary.get("claims_count", 0),
            papers_count=summary.get("papers_count", 0),
        )

    @app.get("/runs")
    async def list_runs(limit: int = 10, _: bool = Depends(verify_token)):
        """List recent runs."""
        from pathlib import Path

        runs_dir = Path("data/runs")
        if not runs_dir.exists():
            return {"runs": []}

        runs = []
        for run_path in sorted(runs_dir.iterdir(), reverse=True)[:limit]:
            if run_path.is_dir():
                runs.append({
                    "run_id": run_path.name,
                })

        return {"runs": runs}


def create_app() -> Optional[FastAPI]:
    """Create and return the FastAPI app."""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")
    return app


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the development server."""
    if not FASTAPI_AVAILABLE:
        print("FastAPI not installed. Run: pip install fastapi uvicorn")
        return

    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
