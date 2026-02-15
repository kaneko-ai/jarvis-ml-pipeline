"""Personal-first Streamlit dashboard for ops_extract operations."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jarvis_core.ops_extract.dashboard.actions import run_cli
from jarvis_core.ops_extract.personal_config import load_personal_config
from jarvis_core.ops_extract.sync_queue import queue_summary


def _import_dashboard_deps():
    import plotly.graph_objects as go
    import streamlit as st

    return st, go


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--run-id", default="")
    args, _ = parser.parse_known_args()
    return args


def _parse_dt(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _format_eta(seconds: float | None) -> str:
    if seconds is None:
        return "N/A"
    total = max(0, int(float(seconds)))
    hh = total // 3600
    mm = (total % 3600) // 60
    ss = total % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def _gauge(go: Any, *, title: str, value: float, max_value: float = 100.0):
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(value),
            title={"text": title},
            gauge={"axis": {"range": [0, max_value]}},
        )
    )
    figure.update_layout(height=260, margin={"t": 40, "b": 20, "l": 20, "r": 20})
    return figure


def _line(go: Any, *, title: str, x: list[str], series: list[tuple[str, list[float]]]):
    figure = go.Figure()
    for name, values in series:
        figure.add_trace(go.Scatter(x=x, y=values, mode="lines+markers", name=name))
    figure.update_layout(
        title=title,
        height=320,
        margin={"t": 60, "b": 30, "l": 30, "r": 20},
        legend={"orientation": "h"},
    )
    return figure


def _discover_runs(runs_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not runs_dir.exists():
        return rows
    for run_path in runs_dir.iterdir():
        if not run_path.is_dir():
            continue
        meta = _load_json(run_path / "run_metadata.json")
        created_at = _parse_dt(meta.get("created_at"))
        if created_at is None:
            created_at = datetime.fromtimestamp(run_path.stat().st_mtime, tz=timezone.utc)
        rows.append(
            {
                "run_id": run_path.name,
                "run_dir": run_path,
                "created_at": created_at,
                "status": str(meta.get("status", "unknown")),
            }
        )
    rows.sort(key=lambda item: item["created_at"], reverse=True)
    return rows


def _resolve_run_dir(
    *,
    args: argparse.Namespace,
    runs_dir: Path,
    run_rows: list[dict[str, Any]],
    selected_run_id: str,
    auto_follow_latest: bool,
) -> Path:
    if args.run_dir:
        return Path(args.run_dir)
    if args.run_id and args.run_id != "latest":
        return runs_dir / str(args.run_id)
    if auto_follow_latest and run_rows:
        return Path(run_rows[0]["run_dir"])
    if selected_run_id:
        return runs_dir / selected_run_id
    if run_rows:
        return Path(run_rows[0]["run_dir"])
    return runs_dir


def _load_paper_totals(counter_path: Path) -> dict[str, int]:
    payload = _load_json(counter_path)
    totals = payload.get("totals", {})
    if not isinstance(totals, dict):
        return {"discovered": 0, "downloaded": 0, "parsed": 0, "indexed": 0}
    return {
        "discovered": int(totals.get("discovered", 0) or 0),
        "downloaded": int(totals.get("downloaded", 0) or 0),
        "parsed": int(totals.get("parsed", 0) or 0),
        "indexed": int(totals.get("indexed", 0) or 0),
    }


def _summarize_24h(run_rows: list[dict[str, Any]]) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    border = now - timedelta(hours=24)
    total = 0
    success = 0
    failed = 0
    for row in run_rows:
        created_at = row.get("created_at")
        if not isinstance(created_at, datetime) or created_at < border:
            continue
        total += 1
        status = str(row.get("status", ""))
        if status == "success":
            success += 1
        elif status == "failed":
            failed += 1
    return {"total": total, "success": success, "failed": failed}


def _open_run_folder(run_dir: Path) -> tuple[int, str, str]:
    if os.name == "nt":
        return run_cli(["powershell", "-NoProfile", "-Command", "explorer", str(run_dir)], 30)
    if sys.platform == "darwin":
        return run_cli(["open", str(run_dir)], 30)
    return run_cli(["xdg-open", str(run_dir)], 30)


def main() -> None:
    st, go = _import_dashboard_deps()
    args = _parse_args()
    personal = load_personal_config()
    runs_dir = Path(personal["runs_dir"])
    queue_dir = Path(personal["queue_dir"])
    paper_counter_path = Path(personal["paper_counter_path"])

    st.set_page_config(page_title="Javis Personal Ops Dashboard", layout="wide")
    st.title("Javis Personal Ops Dashboard")
    st.caption("運用を止めないための個人向け監視・操作画面")

    if hasattr(st, "autorefresh"):
        st.autorefresh(interval=1000, key="javis_personal_ops_refresh")

    run_rows = _discover_runs(runs_dir)
    run_ids = [str(row["run_id"]) for row in run_rows]

    with st.sidebar:
        st.header("Control")
        mode = st.radio(
            "Mode",
            options=["personal", "debug"],
            index=0 if personal.get("dashboard_default_mode") != "debug" else 1,
        )
        auto_follow_latest = st.toggle(
            "Auto-follow latest run",
            value=bool(personal.get("dashboard_autofollow_latest", True)),
        )
        selected_run_id = st.selectbox(
            "Run selector",
            options=run_ids if run_ids else [""],
            index=0,
            format_func=lambda v: "latest" if not v else v,
        )

        queue = queue_summary(queue_dir)
        st.subheader("Queue Summary")
        st.metric("Pending", f"{int(queue.get('pending_count', 0))} items")
        st.metric("Oldest", f"{int(queue.get('oldest_age_days', 0))} days")
        st.metric(
            "Human Action",
            f"{int(queue.get('human_action_required_count', 0))} items",
        )

        st.subheader("Quick Actions")
        action_result = st.session_state.get("action_result", {})
        current_run_for_action = selected_run_id or (run_ids[0] if run_ids else "")

        if st.button("Sync queue now", use_container_width=True):
            action_result = {}
            rc, out, err = run_cli(
                ["javisctl", "sync", "--queue-dir", str(queue_dir)], timeout_sec=300
            )
            action_result = {"name": "sync", "rc": rc, "stdout": out, "stderr": err}
            st.session_state["action_result"] = action_result
        if st.button("Doctor now", use_container_width=True):
            action_result = {}
            rc, out, err = run_cli(
                ["javisctl", "doctor", "--queue-dir", str(queue_dir)], timeout_sec=180
            )
            action_result = {"name": "doctor", "rc": rc, "stdout": out, "stderr": err}
            st.session_state["action_result"] = action_result
        if st.button("Audit drive", use_container_width=True):
            action_result = {}
            if current_run_for_action:
                rc, out, err = run_cli(
                    ["javisctl", "audit", "--run-id", current_run_for_action],
                    timeout_sec=180,
                )
            else:
                rc, out, err = 2, "", "run_id_unavailable"
            action_result = {"name": "audit", "rc": rc, "stdout": out, "stderr": err}
            st.session_state["action_result"] = action_result
        if st.button("Open run folder", use_container_width=True):
            action_result = {}
            candidate = runs_dir / current_run_for_action if current_run_for_action else runs_dir
            rc, out, err = _open_run_folder(candidate)
            action_result = {"name": "open_folder", "rc": rc, "stdout": out, "stderr": err}
            st.session_state["action_result"] = action_result

        if action_result:
            st.caption(f"Action: {action_result.get('name')} rc={action_result.get('rc')}")
            st.code(action_result.get("stdout") or "(no stdout)")
            if action_result.get("stderr"):
                st.code(action_result.get("stderr"))

    run_dir = _resolve_run_dir(
        args=args,
        runs_dir=runs_dir,
        run_rows=run_rows,
        selected_run_id=selected_run_id,
        auto_follow_latest=auto_follow_latest,
    )
    run_id = run_dir.name if run_dir.parent == runs_dir else ""
    telemetry_rows = _load_jsonl(run_dir / "telemetry.jsonl")
    progress_rows = _load_jsonl(run_dir / "progress.jsonl")
    latest_tel = telemetry_rows[-1] if telemetry_rows else {}
    latest_prog = progress_rows[-1] if progress_rows else {}
    papers_total = _load_paper_totals(paper_counter_path)
    papers_run = latest_prog.get("papers_run", {}) if isinstance(latest_prog, dict) else {}
    snapshot_24h = _summarize_24h(run_rows)

    st.subheader("今日の運用スナップショット")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Runs 24h", f"{snapshot_24h['total']} runs")
    c2.metric("Success 24h", f"{snapshot_24h['success']} runs")
    c3.metric("Failed 24h", f"{snapshot_24h['failed']} runs")
    c4.metric("Current Run", run_id or "N/A")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Papers discovered", f"{papers_total['discovered']} papers")
    p2.metric("Papers downloaded", f"{papers_total['downloaded']} papers")
    p3.metric("Papers parsed", f"{papers_total['parsed']} papers")
    p4.metric("Papers indexed", f"{papers_total['indexed']} papers")

    st.subheader("ランタイム監視")
    if telemetry_rows:
        t1, t2, t3, t4 = st.columns(4)
        t1.metric(
            "Network sent", f"{float(latest_tel.get('net_sent_bytes_total', 0))/1024/1024:.2f} MB"
        )
        t2.metric(
            "Network recv", f"{float(latest_tel.get('net_recv_bytes_total', 0))/1024/1024:.2f} MB"
        )
        t3.metric("RSS", f"{float(latest_tel.get('rss_mb', 0.0)):.1f} MB")
        t4.metric("CPU", f"{float(latest_tel.get('cpu_percent', 0.0)):.1f} %")

    g1, g2, g3 = st.columns(3)
    g1.plotly_chart(
        _gauge(go, title="Crash Risk %", value=float(latest_tel.get("crash_risk_percent", 0.0))),
        use_container_width=True,
    )
    g2.plotly_chart(
        _gauge(
            go,
            title="Overall Progress %",
            value=float(latest_prog.get("overall_progress_percent", 0.0)),
        ),
        use_container_width=True,
    )
    g3.plotly_chart(
        _gauge(
            go,
            title="Stage Progress %",
            value=float(latest_prog.get("stage_progress_percent", 0.0)),
        ),
        use_container_width=True,
    )

    eta_a, eta_b = st.columns(2)
    eta_a.metric("ETA", _format_eta(latest_prog.get("eta_seconds")))
    eta_b.metric("ETA Confidence", f"{float(latest_prog.get('eta_confidence_percent', 0.0)):.1f} %")

    if isinstance(papers_run, dict) and papers_run:
        pr1, pr2, pr3, pr4 = st.columns(4)
        pr1.metric("Run discovered", f"{int(papers_run.get('discovered', 0))} papers")
        pr2.metric("Run downloaded", f"{int(papers_run.get('downloaded', 0))} papers")
        pr3.metric("Run parsed", f"{int(papers_run.get('parsed', 0))} papers")
        pr4.metric("Run indexed", f"{int(papers_run.get('indexed', 0))} papers")

    if telemetry_rows:
        tx = [str(row.get("ts_iso", "")) for row in telemetry_rows]
        sent_mb = [
            float(row.get("net_sent_bytes_total", 0.0)) / (1024.0 * 1024.0)
            for row in telemetry_rows
        ]
        recv_mb = [
            float(row.get("net_recv_bytes_total", 0.0)) / (1024.0 * 1024.0)
            for row in telemetry_rows
        ]
        sent_kbps = [float(row.get("net_sent_bps", 0.0)) / 1024.0 for row in telemetry_rows]
        recv_kbps = [float(row.get("net_recv_bps", 0.0)) / 1024.0 for row in telemetry_rows]
        rss_mb = [float(row.get("rss_mb", 0.0)) for row in telemetry_rows]
        cpu_pct = [float(row.get("cpu_percent", 0.0)) for row in telemetry_rows]

        st.plotly_chart(
            _line(
                go,
                title="Network Cumulative (MB)",
                x=tx,
                series=[("sent_mb", sent_mb), ("recv_mb", recv_mb)],
            ),
            use_container_width=True,
        )
        st.plotly_chart(
            _line(
                go,
                title="Network Throughput (KB/s)",
                x=tx,
                series=[("sent_kbps", sent_kbps), ("recv_kbps", recv_kbps)],
            ),
            use_container_width=True,
        )
        st.plotly_chart(
            _line(
                go,
                title="Memory/CPU",
                x=tx,
                series=[("rss_mb", rss_mb), ("cpu_percent", cpu_pct)],
            ),
            use_container_width=True,
        )

    with st.expander("進捗詳細"):
        if progress_rows:
            px = [str(row.get("ts_iso", "")) for row in progress_rows]
            overall = [float(row.get("overall_progress_percent", 0.0)) for row in progress_rows]
            stage = [float(row.get("stage_progress_percent", 0.0)) for row in progress_rows]
            st.plotly_chart(
                _line(
                    go,
                    title="Progress Timeline",
                    x=px,
                    series=[("overall_%", overall), ("stage_%", stage)],
                ),
                use_container_width=True,
            )

            stage_latest: dict[str, float] = {}
            for row in progress_rows:
                stage_name = str(row.get("stage", "")).strip()
                if not stage_name:
                    continue
                stage_latest[stage_name] = max(
                    stage_latest.get(stage_name, 0.0),
                    float(row.get("stage_progress_percent", 0.0)),
                )
            fig = go.Figure(
                go.Bar(
                    x=list(stage_latest.keys()),
                    y=list(stage_latest.values()),
                )
            )
            fig.update_layout(
                title="Stage Progress Snapshot", yaxis={"range": [0, 100]}, height=320
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("progress.jsonl がまだありません。")

    if mode == "debug":
        with st.expander("Debug Payload"):
            st.code(
                json.dumps(
                    {"latest_telemetry": latest_tel, "latest_progress": latest_prog},
                    ensure_ascii=False,
                    indent=2,
                )
            )


if __name__ == "__main__":
    main()
