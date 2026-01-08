"""Slack Integration for JARVIS.

Per RP-533, implements Slack notifications and alerts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageType(Enum):
    """Slack message types."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"


@dataclass
class SlackMessage:
    """A Slack message."""

    channel: str
    text: str
    message_type: MessageType = MessageType.INFO
    attachments: list[dict[str, Any]] = field(default_factory=list)
    blocks: list[dict[str, Any]] = field(default_factory=list)
    thread_ts: str | None = None


class SlackClient:
    """Slack API client.

    Per RP-533:
    - Send notifications
    - Channel management
    - Thread replies
    - Rich formatting
    """

    def __init__(
        self,
        token: str | None = None,
        default_channel: str = "#jarvis-alerts",
    ):
        self.token = token or os.getenv("SLACK_BOT_TOKEN", "")
        self.default_channel = default_channel
        self._enabled = bool(self.token)

    def is_enabled(self) -> bool:
        """Check if Slack is configured."""
        return self._enabled

    def send_message(
        self,
        text: str,
        channel: str | None = None,
        message_type: MessageType = MessageType.INFO,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Send a message to Slack.

        Args:
            text: Message text.
            channel: Target channel.
            message_type: Message type for formatting.
            **kwargs: Additional API parameters.

        Returns:
            API response or None if disabled.
        """
        if not self._enabled:
            return None

        channel = channel or self.default_channel

        # Build message with formatting based on type
        color = self._get_color(message_type)
        emoji = self._get_emoji(message_type)

        payload = {
            "channel": channel,
            "text": f"{emoji} {text}",
            "attachments": [
                {
                    "color": color,
                    "text": text,
                }
            ],
            **kwargs,
        }

        return self._post("chat.postMessage", payload)

    def send_alert(
        self,
        title: str,
        description: str,
        severity: str = "warning",
        fields: dict[str, str] | None = None,
        channel: str | None = None,
    ) -> dict[str, Any] | None:
        """Send an alert to Slack.

        Args:
            title: Alert title.
            description: Alert description.
            severity: Alert severity.
            fields: Additional fields.
            channel: Target channel.

        Returns:
            API response.
        """
        if not self._enabled:
            return None

        channel = channel or self.default_channel
        message_type = self._severity_to_type(severity)
        color = self._get_color(message_type)
        emoji = self._get_emoji(message_type)

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": description,
                },
            },
        ]

        if fields:
            field_blocks = []
            for key, value in fields.items():
                field_blocks.append(
                    {
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}",
                    }
                )

            blocks.append(
                {
                    "type": "section",
                    "fields": field_blocks[:10],  # Max 10 fields
                }
            )

        payload = {
            "channel": channel,
            "text": f"{emoji} {title}: {description}",
            "blocks": blocks,
            "attachments": [{"color": color, "blocks": []}],
        }

        return self._post("chat.postMessage", payload)

    def send_pipeline_update(
        self,
        pipeline_id: str,
        status: str,
        progress: float,
        message: str | None = None,
        channel: str | None = None,
    ) -> dict[str, Any] | None:
        """Send pipeline status update.

        Args:
            pipeline_id: Pipeline ID.
            status: Current status.
            progress: Progress (0-1).
            message: Optional message.
            channel: Target channel.

        Returns:
            API response.
        """
        progress_bar = self._make_progress_bar(progress)

        text = f"Pipeline `{pipeline_id}`: {status}\n{progress_bar}"
        if message:
            text += f"\n{message}"

        message_type = MessageType.SUCCESS if status == "completed" else MessageType.INFO

        return self.send_message(text, channel, message_type)

    def _make_progress_bar(self, progress: float, width: int = 20) -> str:
        """Create ASCII progress bar."""
        filled = int(progress * width)
        empty = width - filled
        bar = "█" * filled + "░" * empty
        return f"[{bar}] {int(progress * 100)}%"

    def _get_color(self, message_type: MessageType) -> str:
        """Get color for message type."""
        colors = {
            MessageType.INFO: "#2196F3",
            MessageType.SUCCESS: "#4CAF50",
            MessageType.WARNING: "#FF9800",
            MessageType.ERROR: "#F44336",
            MessageType.ALERT: "#9C27B0",
        }
        return colors.get(message_type, "#2196F3")

    def _get_emoji(self, message_type: MessageType) -> str:
        """Get emoji for message type."""
        emojis = {
            MessageType.INFO: "ℹ️",
            MessageType.SUCCESS: "✅",
            MessageType.WARNING: "⚠️",
            MessageType.ERROR: "❌",
            MessageType.ALERT: "🚨",
        }
        return emojis.get(message_type, "ℹ️")

    def _severity_to_type(self, severity: str) -> MessageType:
        """Convert severity to message type."""
        mapping = {
            "info": MessageType.INFO,
            "success": MessageType.SUCCESS,
            "warning": MessageType.WARNING,
            "error": MessageType.ERROR,
            "critical": MessageType.ALERT,
        }
        return mapping.get(severity.lower(), MessageType.INFO)

    def _post(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Post to Slack API.

        Args:
            endpoint: API endpoint.
            payload: Request payload.

        Returns:
            API response.
        """
        # In production, use httpx/requests
        # This is a mock implementation
        return {
            "ok": True,
            "channel": payload.get("channel"),
            "ts": "1234567890.123456",
            "message": payload,
        }


# Global client
_slack_client: SlackClient | None = None


def get_slack_client() -> SlackClient:
    """Get global Slack client."""
    global _slack_client
    if _slack_client is None:
        _slack_client = SlackClient()
    return _slack_client


def notify_slack(
    text: str,
    channel: str | None = None,
    message_type: MessageType = MessageType.INFO,
) -> dict[str, Any] | None:
    """Quick notification helper."""
    return get_slack_client().send_message(text, channel, message_type)
