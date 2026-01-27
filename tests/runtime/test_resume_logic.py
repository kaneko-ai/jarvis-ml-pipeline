from jarvis_core.runtime.checkpoint import CheckpointManager


def test_checkpoint_lifecycle(tmp_path):
    run_id = "run_123"
    cp_dir = tmp_path / "checkpoints"

    # 1. Initialize
    mgr = CheckpointManager(cp_dir, run_id)
    assert mgr.state.current_stage == "init"

    # 2. Update state
    mgr.set_stage("crawling")
    mgr.mark_processed("item_1")
    mgr.mark_processed("item_2")
    mgr.mark_failed("item_3", "Timeout")
    mgr.save()

    # Verify file exists
    cp_file = cp_dir / f"{run_id}_checkpoint.json"
    assert cp_file.exists()

    # 3. Resume (Load from disk)
    mgr_new = CheckpointManager(cp_dir, run_id)
    assert mgr_new.state.current_stage == "crawling"
    assert mgr_new.is_processed("item_1")
    assert mgr_new.is_processed("item_2")
    assert not mgr_new.is_processed("item_4")
    assert mgr_new.state.failed_items["item_3"] == "Timeout"


def test_checkpoint_isolation(tmp_path):
    mgr1 = CheckpointManager(tmp_path, "run_A")
    mgr2 = CheckpointManager(tmp_path, "run_B")

    mgr1.set_stage("A_stage")
    mgr2.set_stage("B_stage")

    assert mgr1.state.current_stage == "A_stage"
    assert mgr2.state.current_stage == "B_stage"

    # Reload
    mgr1_loaded = CheckpointManager(tmp_path, "run_A")
    assert mgr1_loaded.state.current_stage == "A_stage"
