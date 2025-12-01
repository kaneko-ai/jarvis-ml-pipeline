"""Minimal FastAPI wrapper to expose Jarvis Core over HTTP."""

from typing import Optional

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


class LiteratureSurveyRequest(BaseModel):
    topic: str
    max_papers: int = 10
    language: Optional[str] = "ja"  # "ja" or "en"


class LiteratureSurveyResponse(BaseModel):
    summary: str


@app.post("/literature-survey", response_model=LiteratureSurveyResponse)
def literature_survey(req: LiteratureSurveyRequest) -> LiteratureSurveyResponse:
    """Run a literature survey via Jarvis."""
    language = req.language or "ja"
    prompt = f"""
You are a biomedical literature survey assistant.

Topic: {req.topic}
Maximum papers: {req.max_papers}

Instructions:
1) Propose three candidate PubMed search queries for the topic.
2) List up to {req.max_papers} representative papers as bullet points with: first author et al., year, journal, and a one-line summary.
3) Summarize the research trajectory in rough chronological order.
4) Provide 3-5 open questions or future directions.
5) Suggest 2-3 hypotheses on how this connects to CD73 and antibody drug discovery.

Output language: {"Japanese" if language == "ja" else "English"}. Ensure the entire response is written in this language.
"""
    result = run_jarvis(prompt)
    return LiteratureSurveyResponse(summary=result)
