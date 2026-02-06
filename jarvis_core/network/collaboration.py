"""Collaboration helpers for network workflows."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CollaborationSession:
    """Simple collaboration session container."""

    session_id: str = ""
    participants: list[str] = field(default_factory=list)


class CollaborationManager:
    """Manage collaboration sessions."""

    def start_session(self, participants: list[str]) -> CollaborationSession:
        """Start a new session with participants.

        Args:
            participants: List of participant identifiers.

        Returns:
            CollaborationSession instance.
        """
        return CollaborationSession(session_id="local", participants=list(participants))

    def end_session(self, session: CollaborationSession) -> None:
        """End a session.

        Args:
            session: Session to end.
        """
        session.participants.clear()


__all__ = ["CollaborationManager", "CollaborationSession"]
