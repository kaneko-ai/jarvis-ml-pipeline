"""Finance routes for P10 optimization."""
from __future__ import annotations

from typing import List, Optional

try:
    from fastapi import APIRouter, HTTPException
    from fastapi.responses import FileResponse, PlainTextResponse
    from pydantic import BaseModel

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = None
    BaseModel = object

from jarvis_core.finance.scenarios import default_scenarios
from jarvis_core.optimization.solver import optimize_scenarios
from jarvis_core.optimization.report import build_report
from jarvis_core.time.schema import default_week_allocation
from jarvis_core.export.package_builder import build_finance_package


class SimulateRequest(BaseModel):
    start_month: str = "2025-04"
    months: int = 36
    planned_research_hours: int = 45


class OptimizeResponse(BaseModel):
    scenario: str
    status: str
    expected_balance_end: int
    bankruptcy_risk: float
    research_hours_avg: float
    overwork_risk: float
    recommendation: str
    note: str = "（推測です）"


router = APIRouter() if FASTAPI_AVAILABLE else None


if FASTAPI_AVAILABLE:

    @router.post("/api/finance/simulate", response_model=List[OptimizeResponse])
    async def simulate_finance(payload: SimulateRequest) -> List[OptimizeResponse]:
        scenarios = default_scenarios(payload.start_month, payload.months)
        allocation = default_week_allocation()
        results = optimize_scenarios(scenarios, allocation, payload.planned_research_hours)
        return [
            OptimizeResponse(
                scenario=result.scenario,
                status=result.status,
                expected_balance_end=result.expected_balance_end,
                bankruptcy_risk=result.bankruptcy_risk,
                research_hours_avg=result.research_hours_avg,
                overwork_risk=result.overwork_risk,
                recommendation=result.recommendation,
            )
            for result in results
        ]

    @router.post("/api/finance/optimize", response_model=OptimizeResponse)
    async def optimize_finance(payload: SimulateRequest) -> OptimizeResponse:
        scenarios = default_scenarios(payload.start_month, payload.months)
        allocation = default_week_allocation()
        results = optimize_scenarios(scenarios, allocation, payload.planned_research_hours)
        if not results:
            raise HTTPException(status_code=404, detail="No scenarios available")
        best = sorted(results, key=lambda r: (r.status != "feasible", r.bankruptcy_risk))[0]
        return OptimizeResponse(
            scenario=best.scenario,
            status=best.status,
            expected_balance_end=best.expected_balance_end,
            bankruptcy_risk=best.bankruptcy_risk,
            research_hours_avg=best.research_hours_avg,
            overwork_risk=best.overwork_risk,
            recommendation=best.recommendation,
        )

    @router.get("/api/finance/report")
    async def finance_report(format: Optional[str] = "md"):
        scenarios = default_scenarios()
        allocation = default_week_allocation()
        results = optimize_scenarios(scenarios, allocation, allocation.variable.research.target)
        fmt = "html" if format == "html" else "md"
        report_text = build_report(results, format=fmt)
        media_type = "text/html" if fmt == "html" else "text/markdown"
        return PlainTextResponse(report_text, media_type=media_type)

    @router.get("/api/finance/download")
    async def finance_download(format: Optional[str] = "md"):
        scenarios = default_scenarios()
        allocation = default_week_allocation()
        results = optimize_scenarios(scenarios, allocation, allocation.variable.research.target)
        fmt = "html" if format == "html" else "md"
        zip_path = build_finance_package(results, format=fmt)
        return FileResponse(zip_path, filename="finance_report.zip")
