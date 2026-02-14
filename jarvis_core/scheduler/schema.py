"""Scheduler schema definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ScheduleQuery(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    mesh: list[str] = Field(default_factory=list)
    date_range_days: int = 30
    oa_only: bool = True
    oa_policy: str = "strict"
    max_papers: int = 50
    sort: str = "pub_date_desc"
    force_refresh: bool = False

    @field_validator("oa_policy")
    @classmethod
    def validate_oa_policy(cls, value: str) -> str:
        if value not in {"strict", "lenient"}:
            raise ValueError("oa_policy must be strict or lenient")
        return value


class ScheduleOutputs(BaseModel):
    rank_top_k: int = 50
    generate_notes: bool = True
    generate_package_zip: bool = True
    generate_submission_package: bool = False


class ScheduleLimits(BaseModel):
    max_runtime_minutes: int = 60
    max_retries: int = 3
    cooldown_minutes_after_failure: int = 30


class ScheduleModel(BaseModel):
    schedule_id: str
    enabled: bool = True
    name: str
    timezone: str = "UTC"
    rrule: str
    pipeline: str = "research_autopilot_v1"
    query: ScheduleQuery
    outputs: ScheduleOutputs = Field(default_factory=ScheduleOutputs)
    limits: ScheduleLimits = Field(default_factory=ScheduleLimits)
    tags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    degraded: bool = False


class ScheduleRun(BaseModel):
    run_id: str
    schedule_id: str
    status: str
    idempotency_key: str
    payload: dict[str, Any]
    attempts: int = 0
    created_at: str
    updated_at: str
    next_retry_at: str | None = None
    error: str | None = None
    job_id: str | None = None


REQUIRED_FIELDS = {"name", "rrule", "query"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_schedule_payload(
    payload: dict[str, Any], schedule_id: str, existing: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = {**(existing or {}), **payload}
    data.setdefault("schedule_id", schedule_id)
    data.setdefault("enabled", True)
    data.setdefault("timezone", "UTC")
    data.setdefault("pipeline", "research_autopilot_v1")
    data.setdefault("query", {})
    data.setdefault("outputs", {})
    data.setdefault("limits", {})
    data.setdefault("tags", [])
    data.setdefault("degraded", False)

    if not existing:
        data.setdefault("created_at", _now())
    data["updated_at"] = _now()

    model = ScheduleModel(
        schedule_id=data["schedule_id"],
        enabled=bool(data.get("enabled", True)),
        name=data.get("name", ""),
        timezone=data.get("timezone", "UTC"),
        rrule=data.get("rrule", ""),
        pipeline=data.get("pipeline", "research_autopilot_v1"),
        query=ScheduleQuery(**data.get("query", {})),
        outputs=ScheduleOutputs(**data.get("outputs", {})),
        limits=ScheduleLimits(**data.get("limits", {})),
        tags=data.get("tags", []),
        created_at=data.get("created_at", _now()),
        updated_at=data.get("updated_at", _now()),
        degraded=bool(data.get("degraded", False)),
    )
    return model.model_dump()


def validate_required_fields(payload: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not payload.get(field)]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
