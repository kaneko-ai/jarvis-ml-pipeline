"""Integrations package for knowledge management tools.

Provides exporters for:
- NotebookLM
- Obsidian
- Notion
- Watch mode
- Slack (RP-533)
- PagerDuty (RP-534)
"""

from .obsidian_sync import ObsidianSync, sync_to_obsidian
from .pagerduty import (
    EventAction,
    PagerDutyClient,
    PagerDutyEvent,
    Severity,
    get_pagerduty_client,
    page,
)
from .slack import (
    MessageType,
    SlackClient,
    SlackMessage,
    get_slack_client,
    notify_slack,
)
from .watch import ManifestWatcher, watch_manifest

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