"""One-command diagnostics and recovery summary for ops_extract."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .contracts import OpsExtractConfig
from .network import detect_network_profile
from .scoreboard import generate_weekly_report
from .sync_queue import load_sync_queue


def run_doctor(
    *,
    config: OpsExtractConfig,
    queue_dir: Path | None = None,
    reports_dir: Path = Path("reports/doctor"),
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    profile, diagnosis = detect_network_profile(config)
    queue_items = load_sync_queue(queue_dir or Path(config.sync_queue_dir))
    failed_items = [
        item
        for item in queue_items
        if str(item.get("state", "")) in {"failed", "human_action_required"}
    ]
    score = generate_weekly_report()
    drive_api_reachable = bool(diagnosis.get("drive_api_reachable"))
    next_commands: list[str] = []
    next_notes: list[str] = []
    if len(failed_items) > 0:
        next_commands.append("javisctl sync --only-human-action")
    elif len(queue_items) > 0:
        next_commands.append("javisctl sync")
    elif not drive_api_reachable:
        next_commands.append("javisctl doctor")
        next_notes.append("network_hint: ネットワーク復旧後に再実行してください。")
    elif score.ops_score < 70 or score.extract_score < 70:
        next_commands.append("javisctl weekly-report")
    else:
        next_commands.append("javisctl weekly-report")

    report_path = reports_dir / f"{now.strftime('%Y%m%dT%H%M%SZ')}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Ops+Extract Doctor Report\n\n")
        f.write(f"- timestamp: {now.isoformat()}\n")
        f.write(f"- network_profile: {profile}\n")
        f.write(f"- drive_api_reachable: {drive_api_reachable}\n")
        f.write(f"- queue_total: {len(queue_items)}\n")
        f.write(f"- queue_human_action_required: {len(failed_items)}\n")
        f.write(f"- ops_score: {score.ops_score}\n")
        f.write(f"- extract_score: {score.extract_score}\n")
        if failed_items:
            f.write("\n## human_action_required\n")
            for item in failed_items[:20]:
                f.write(
                    f"- run_id={item.get('run_id','')} state={item.get('state','')} "
                    f"error={item.get('last_error','')}\n"
                )
        f.write("\n## Next Commands\n")
        for command in next_commands:
            f.write(f"- `{command}`\n")
        for note in next_notes:
            f.write(f"- {note}\n")
    return report_path
