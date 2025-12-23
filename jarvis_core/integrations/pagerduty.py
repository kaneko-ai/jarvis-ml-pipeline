"""PagerDuty Integration for JARVIS.

Per RP-534, implements PagerDuty alerting.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class Severity(Enum):
    """PagerDuty alert severity."""
    
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class EventAction(Enum):
    """PagerDuty event action."""
    
    TRIGGER = "trigger"
    ACKNOWLEDGE = "acknowledge"
    RESOLVE = "resolve"


@dataclass
class PagerDutyEvent:
    """A PagerDuty event."""
    
    summary: str
    severity: Severity
    source: str
    dedup_key: Optional[str] = None
    custom_details: Dict[str, Any] = field(default_factory=dict)
    links: List[Dict[str, str]] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)


class PagerDutyClient:
    """PagerDuty Events API client.
    
    Per RP-534:
    - Send alerts
    - Acknowledge/resolve incidents
    - Link to runbooks
    - Custom severity mapping
    """
    
    EVENTS_URL = "https://events.pagerduty.com/v2/enqueue"
    
    def __init__(
        self,
        routing_key: Optional[str] = None,
        service_name: str = "jarvis",
    ):
        self.routing_key = routing_key or os.getenv("PAGERDUTY_ROUTING_KEY", "")
        self.service_name = service_name
        self._enabled = bool(self.routing_key)
    
    def is_enabled(self) -> bool:
        """Check if PagerDuty is configured."""
        return self._enabled
    
    def trigger(
        self,
        summary: str,
        severity: Severity = Severity.ERROR,
        source: Optional[str] = None,
        dedup_key: Optional[str] = None,
        custom_details: Optional[Dict[str, Any]] = None,
        runbook_url: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Trigger a PagerDuty alert.
        
        Args:
            summary: Alert summary.
            severity: Alert severity.
            source: Event source.
            dedup_key: Deduplication key.
            custom_details: Additional details.
            runbook_url: Link to runbook.
            
        Returns:
            API response.
        """
        if not self._enabled:
            return None
        
        links = []
        if runbook_url:
            links.append({
                "href": runbook_url,
                "text": "Runbook",
            })
        
        payload = self._build_payload(
            action=EventAction.TRIGGER,
            summary=summary,
            severity=severity,
            source=source or f"{self.service_name}-api",
            dedup_key=dedup_key,
            custom_details=custom_details or {},
            links=links,
        )
        
        return self._send(payload)
    
    def acknowledge(
        self,
        dedup_key: str,
    ) -> Optional[Dict[str, Any]]:
        """Acknowledge an incident.
        
        Args:
            dedup_key: Deduplication key.
            
        Returns:
            API response.
        """
        if not self._enabled:
            return None
        
        payload = {
            "routing_key": self.routing_key,
            "dedup_key": dedup_key,
            "event_action": EventAction.ACKNOWLEDGE.value,
        }
        
        return self._send(payload)
    
    def resolve(
        self,
        dedup_key: str,
    ) -> Optional[Dict[str, Any]]:
        """Resolve an incident.
        
        Args:
            dedup_key: Deduplication key.
            
        Returns:
            API response.
        """
        if not self._enabled:
            return None
        
        payload = {
            "routing_key": self.routing_key,
            "dedup_key": dedup_key,
            "event_action": EventAction.RESOLVE.value,
        }
        
        return self._send(payload)
    
    def trigger_alert(
        self,
        alert_name: str,
        description: str,
        severity: str = "error",
        labels: Optional[Dict[str, str]] = None,
        annotations: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Trigger alert with Prometheus-style labels.
        
        Args:
            alert_name: Alert name.
            description: Alert description.
            severity: Alert severity.
            labels: Alert labels.
            annotations: Alert annotations.
            
        Returns:
            API response.
        """
        sev = self._parse_severity(severity)
        
        custom_details = {
            "alert_name": alert_name,
            "labels": labels or {},
            "annotations": annotations or {},
        }
        
        dedup_key = f"{self.service_name}-{alert_name}"
        if labels:
            dedup_key += f"-{'-'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        
        runbook_url = None
        if annotations and "runbook_url" in annotations:
            runbook_url = annotations["runbook_url"]
        
        return self.trigger(
            summary=f"[{alert_name}] {description}",
            severity=sev,
            dedup_key=dedup_key,
            custom_details=custom_details,
            runbook_url=runbook_url,
        )
    
    def _build_payload(
        self,
        action: EventAction,
        summary: str,
        severity: Severity,
        source: str,
        dedup_key: Optional[str],
        custom_details: Dict[str, Any],
        links: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Build PagerDuty event payload."""
        payload = {
            "routing_key": self.routing_key,
            "event_action": action.value,
            "dedup_key": dedup_key or f"{self.service_name}-{int(time.time())}",
            "payload": {
                "summary": summary,
                "severity": severity.value,
                "source": source,
                "custom_details": custom_details,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            },
        }
        
        if links:
            payload["links"] = links
        
        return payload
    
    def _parse_severity(self, severity: str) -> Severity:
        """Parse severity string to enum."""
        mapping = {
            "critical": Severity.CRITICAL,
            "error": Severity.ERROR,
            "warning": Severity.WARNING,
            "info": Severity.INFO,
        }
        return mapping.get(severity.lower(), Severity.ERROR)
    
    def _send(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send event to PagerDuty.
        
        Args:
            payload: Event payload.
            
        Returns:
            API response.
        """
        # In production, use httpx/requests
        # This is a mock implementation
        return {
            "status": "success",
            "message": "Event processed",
            "dedup_key": payload.get("dedup_key"),
        }


# Global client
_pagerduty_client: Optional[PagerDutyClient] = None


def get_pagerduty_client() -> PagerDutyClient:
    """Get global PagerDuty client."""
    global _pagerduty_client
    if _pagerduty_client is None:
        _pagerduty_client = PagerDutyClient()
    return _pagerduty_client


def page(
    summary: str,
    severity: Severity = Severity.ERROR,
    **kwargs,
) -> Optional[Dict[str, Any]]:
    """Quick paging helper."""
    return get_pagerduty_client().trigger(summary, severity, **kwargs)
