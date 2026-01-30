from jarvis_core.feedback.store import FeedbackStore


def test_log_and_load(tmp_path):
    store = FeedbackStore(tmp_path)

    store.log_feedback("q1", "d1", 5, {"context": "test"})
    store.log_feedback("q1", "d2", 1)

    items = store.load_recent()
    assert len(items) == 2

    assert items[0]["query_id"] == "q1"
    assert items[0]["doc_id"] == "d1"
    assert items[0]["rating"] == 5

    assert items[1]["doc_id"] == "d2"
    assert items[1]["rating"] == 1


def test_persistence(tmp_path):
    store = FeedbackStore(tmp_path)
    store.log_feedback("q_persist", "d_persist", 3)

    # Reload from disk
    store2 = FeedbackStore(tmp_path)
    items = store2.load_recent()

    assert len(items) == 1
    assert items[0]["query_id"] == "q_persist"


def test_empty_load(tmp_path):
    store = FeedbackStore(tmp_path)
    items = store.load_recent()
    assert len(items) == 0
