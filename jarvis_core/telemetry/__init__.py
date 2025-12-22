"""Telemetry package for structured logging."""
from .schema import TelemetryEvent, EventType
from .logger import JsonlTelemetryLogger, get_logger, init_logger
from .hashing import prompt_hash, input_hash, normalize_text

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

