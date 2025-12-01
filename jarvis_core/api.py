"""Minimal FastAPI wrapper to expose Jarvis Core over HTTP."""

from fastapi import FastAPI
from pydantic import BaseModel

from jarvis_core import run_jarvis

app = FastAPI(title="Jarvis Core API", version="0.1.0")


class JarvisRequest(BaseModel):
    goal: str


class JarvisResponse(BaseModel):
    answer: str


@app.post("/jarvis", response_model=JarvisResponse)
def call_jarvis(req: JarvisRequest) -> JarvisResponse:
    """Handle incoming Jarvis requests via HTTP."""
    result = run_jarvis(req.goal)
    return JarvisResponse(answer=result)
