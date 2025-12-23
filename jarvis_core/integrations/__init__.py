"""Integrations package for knowledge management tools.

Provides exporters for:
- NotebookLM
- Obsidian
- Notion
- Watch mode
- Slack (RP-533)
- PagerDuty (RP-534)
"""
from .obsidian_sync import sync_to_obsidian, ObsidianSync
from .watch import watch_manifest, ManifestWatcher
from .slack import (
    SlackClient,
    SlackMessage,
    MessageType,
    get_slack_client,
    notify_slack,
)
from .pagerduty import (
    PagerDutyClient,
    PagerDutyEvent,
    Severity,
    EventAction,
    get_pagerduty_client,
    page,
)

__all__ = [
    "sync_to_obsidian",
    "ObsidianSync",
    "watch_manifest",
    "ManifestWatcher",
    # Slack
    "SlackClient",
    "SlackMessage",
    "MessageType",
    "get_slack_client",
    "notify_slack",
    # PagerDuty
    "PagerDutyClient",
    "PagerDutyEvent",
    "Severity",
    "EventAction",
    "get_pagerduty_client",
    "page",
]
