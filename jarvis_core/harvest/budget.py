"""Budget parsing and checks for harvest commands."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class HarvestBudget:
    max_items: int = 200
    max_minutes: int = 30
    max_requests: int = 400
    started_at: datetime | None = None
    items_done: int = 0
    requests_done: int = 0

    def start(self) -> None:
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)

    def consume_item(self) -> None:
        self.items_done += 1

    def consume_request(self, count: int = 1) -> None:
        self.requests_done += count

    def is_exceeded(self) -> bool:
        if self.items_done >= self.max_items:
            return True
        if self.requests_done >= self.max_requests:
            return True
        if self.started_at is None:
            return False
        elapsed_minutes = (datetime.now(timezone.utc) - self.started_at).total_seconds() / 60.0
        return elapsed_minutes >= self.max_minutes


def parse_budget(raw: str | None) -> HarvestBudget:
    if not raw:
        return HarvestBudget()
    parts = {}
    for token in raw.split(","):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        parts[key.strip()] = value.strip()
    return HarvestBudget(
        max_items=int(parts.get("max_items", 200)),
        max_minutes=int(parts.get("max_minutes", 30)),
        max_requests=int(parts.get("max_requests", 400)),
    )
