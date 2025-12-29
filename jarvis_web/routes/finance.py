"""Finance and optimization API endpoints."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse

from jarvis_core.decision.planner import assess_plan_time
from jarvis_core.export.package_builder import build_finance_package
from jarvis_core.finance.scenarios import build_scenarios
from jarvis_core.optimization.report import generate_html, generate_markdown
from jarvis_core.optimization.solver import choose_best, optimize
from jarvis_core.time.schema import DEFAULT_TIME_SCHEMA, TimeSchema, VariableBlock


router = APIRouter()


def _parse_time_schema(payload: Dict[str, Any]) -> TimeSchema:
    time_payload = payload.get("time")
    if not time_payload:
        return DEFAULT_TIME_SCHEMA
    fixed = time_payload.get("fixed", DEFAULT_TIME_SCHEMA.fixed)
    variable_payload = time_payload.get("variable", {})
    variable = {}
    for key, value in variable_payload.items():
        variable[key] = VariableBlock(
            min=value.get("min", 0.0),
            target=value.get("target", 0.0),
            max=value.get("max", 0.0),
        )
    for key, block in DEFAULT_TIME_SCHEMA.variable.items():
        variable.setdefault(key, block)
    return TimeSchema(
        week_hours=time_payload.get("week_hours", DEFAULT_TIME_SCHEMA.week_hours),
        fixed=fixed,
        variable=variable,
    )


def _scenario_summary(cashflows) -> Dict[str, Any]:
    monthly = []
    deficit_months = []
    for flow in cashflows:
        expected_end = flow.expected_balance_end()
        downside_end = flow.downside_balance_end()
        monthly.append(
            {
                "month": flow.month,
                "expected_balance_end": expected_end,
                "downside_balance_end": downside_end,
            }
        )
        if downside_end < 0:
            deficit_months.append(flow.month)
    worst_month = deficit_months[0] if deficit_months else None
    return {
        "monthly": monthly,
        "deficit_months": deficit_months,
        "worst_case_deficit_month": worst_month,
    }


def _serialize_evaluation(evaluation) -> Dict[str, Any]:
    return {
        "scenario": evaluation.scenario,
        "status": evaluation.status,
        "expected_balance_end": evaluation.expected_balance_end,
        "bankruptcy_risk": evaluation.bankruptcy_risk,
        "research_hours_avg": evaluation.research_hours_avg,
        "overwork_risk": evaluation.overwork_risk,
        "minimum_balance": evaluation.minimum_balance,
        "recommendation": evaluation.recommendation,
        "hard_violations": [v.detail for v in evaluation.constraint_report.hard_violations],
        "soft_violations": [v.detail for v in evaluation.constraint_report.soft_violations],
    }


@router.post("/api/finance/simulate")
async def simulate(payload: Dict[str, Any] = Body(default_factory=dict)):
    months = int(payload.get("months", 36))
    start_month = payload.get("start_month")
    savings_start = float(payload.get("savings_start", 300000))
    scenarios = build_scenarios(months=months, start_month=start_month, savings_start=savings_start)
    time_schema = _parse_time_schema(payload)
    plan = payload.get("plan", {})
    plan_assessment = assess_plan_time(plan, time_schema)
    evaluations = optimize(
        scenarios,
        time_schema,
        plan_assessment.required_research_hours,
        plan_assessment.delay_cost,
    )

    response_scenarios: List[Dict[str, Any]] = []
    for scenario_id, result in scenarios.items():
        evaluation = evaluations[scenario_id]
        response_scenarios.append(
            {
                "scenario": scenario_id,
                "name": result.name,
                "status": evaluation.status,
                "expected_balance_end": evaluation.expected_balance_end,
                "bankruptcy_risk": evaluation.bankruptcy_risk,
                "research_hours_avg": evaluation.research_hours_avg,
                "overwork_risk": evaluation.overwork_risk,
                "minimum_balance": evaluation.minimum_balance,
                "recommendation": evaluation.recommendation,
                "summary": _scenario_summary(result.cashflows),
            }
        )

    return JSONResponse(
        {
            "assumption_note": "（推測です）",
            "plan_assessment": plan_assessment.__dict__,
            "scenarios": response_scenarios,
        }
    )


@router.post("/api/finance/optimize")
async def optimize_finance(payload: Dict[str, Any] = Body(default_factory=dict)):
    months = int(payload.get("months", 36))
    start_month = payload.get("start_month")
    savings_start = float(payload.get("savings_start", 300000))
    scenarios = build_scenarios(months=months, start_month=start_month, savings_start=savings_start)
    time_schema = _parse_time_schema(payload)
    plan = payload.get("plan", {})
    plan_assessment = assess_plan_time(plan, time_schema)
    evaluations = optimize(
        scenarios,
        time_schema,
        plan_assessment.required_research_hours,
        plan_assessment.delay_cost,
    )
    best = choose_best(evaluations)
    return JSONResponse(
        {
            "assumption_note": "（推測です）",
            "status": best.status,
            "scenario": best.scenario,
            "expected_balance_end": best.expected_balance_end,
            "bankruptcy_risk": best.bankruptcy_risk,
            "research_hours_avg": best.research_hours_avg,
            "overwork_risk": best.overwork_risk,
            "recommendation": best.recommendation,
            "plan_assessment": plan_assessment.__dict__,
        }
    )


@router.get("/api/finance/report")
async def finance_report(format: str = Query("md")):
    scenarios = build_scenarios()
    evaluations = optimize(scenarios, DEFAULT_TIME_SCHEMA)
    if format == "md":
        report = generate_markdown(scenarios, evaluations)
        return PlainTextResponse(report, media_type="text/markdown")
    if format == "html":
        report = generate_html(scenarios, evaluations)
        return PlainTextResponse(report, media_type="text/html")
    return JSONResponse({"error": "unsupported format"}, status_code=400)


@router.get("/api/finance/download")
async def finance_download(format: str = Query("zip")):
    if format != "zip":
        return JSONResponse({"error": "unsupported format"}, status_code=400)
    scenarios = build_scenarios()
    evaluations = optimize(scenarios, DEFAULT_TIME_SCHEMA)
    report_md = generate_markdown(scenarios, evaluations)
    report_html = generate_html(scenarios, evaluations)
    data = {
        "scenarios": {
            scenario_id: {
                "name": result.name,
                "months": [flow.month for flow in result.cashflows],
            }
            for scenario_id, result in scenarios.items()
        },
        "evaluations": {
            scenario_id: _serialize_evaluation(evaluation)
            for scenario_id, evaluation in evaluations.items()
        },
    }
    package_path = build_finance_package(report_md, report_html, data)
    return FileResponse(
        package_path,
        media_type="application/zip",
        filename="finance_report.zip",
    )
