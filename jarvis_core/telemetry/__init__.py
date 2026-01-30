"""Telemetry package for structured logging."""

from .hashing import input_hash, normalize_text, prompt_hash
from .logger import JsonlTelemetryLogger, get_logger, init_logger
from .schema import EventType, TelemetryEvent

__all__ = [
    "TelemetryEvent",
    "EventType",
    "JsonlTelemetryLogger",
    "get_logger",
    "init_logger",
    "prompt_hash",
    "input_hash",
    "normalize_text",
]