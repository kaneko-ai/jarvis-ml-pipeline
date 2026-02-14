"""Mentions and comments support for artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
import uuid


@dataclass
class Selection:
    start: int
    end: int
    text: str | None = None


@dataclass
class Comment:
    comment_id: str
    artifact_id: str
    user_id: str
    content: str
    selection: Selection | None
    mentions: list[str]
    created_at: str
    resolved: bool = False


class CommentStore:
    """In-memory comment store."""

    def __init__(self):
        self._comments: dict[str, Comment] = {}
        self._by_artifact: dict[str, list[str]] = {}

    def add_comment(
        self,
        artifact_id: str,
        user_id: str,
        content: str,
        selection: Selection | None,
    ) -> Comment:
        comment_id = str(uuid.uuid4())
        mentions = re.findall(r"@(\w+)", content)
        comment = Comment(
            comment_id=comment_id,
            artifact_id=artifact_id,
            user_id=user_id,
            content=content,
            selection=selection,
            mentions=mentions,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        )
        self._comments[comment_id] = comment
        self._by_artifact.setdefault(artifact_id, []).append(comment_id)
        return comment

    def resolve_comment(self, comment_id: str) -> None:
        comment = self._comments.get(comment_id)
        if comment:
            comment.resolved = True

    def list_comments(self, artifact_id: str) -> list[Comment]:
        return [self._comments[cid] for cid in self._by_artifact.get(artifact_id, [])]
