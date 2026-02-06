"""Scheduler helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScheduledJob:
    """Scheduled job metadata."""

    job_id: str
    name: str


class Scheduler:
    """Minimal scheduler stub."""

    def schedule(self, name: str) -> ScheduledJob:
        """Schedule a job.

        Args:
            name: Job name.

        Returns:
            ScheduledJob instance.
        """
        return ScheduledJob(job_id=name, name=name)


__all__ = ["ScheduledJob", "Scheduler"]
