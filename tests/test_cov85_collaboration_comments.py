from __future__ import annotations

from jarvis_core.collaboration.comments import CommentStore, Selection


def test_comment_store_add_list_and_mentions() -> None:
    store = CommentStore()
    selection = Selection(start=1, end=4, text="abc")

    comment = store.add_comment(
        artifact_id="a1",
        user_id="u1",
        content="Please check @alice and @bob",
        selection=selection,
    )

    assert comment.artifact_id == "a1"
    assert comment.user_id == "u1"
    assert comment.mentions == ["alice", "bob"]
    listed = store.list_comments("a1")
    assert len(listed) == 1
    assert listed[0].comment_id == comment.comment_id


def test_comment_store_resolve_and_missing_artifact() -> None:
    store = CommentStore()
    comment = store.add_comment(
        artifact_id="a2",
        user_id="u2",
        content="No mention",
        selection=None,
    )

    assert comment.resolved is False
    store.resolve_comment(comment.comment_id)
    assert store.list_comments("a2")[0].resolved is True

    # no-op path
    store.resolve_comment("missing")
    assert store.list_comments("unknown") == []
