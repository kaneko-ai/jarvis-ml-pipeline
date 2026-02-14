"""Streamlit dashboard for ops_extract telemetry/progress."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--run-id", default="")
    args, _ = parser.parse_known_args()
    return args


def _resolve_run_dir(args: argparse.Namespace) -> Path:
    if args.run_dir:
        return Path(args.run_dir)
    if args.run_id:
        return Path("logs") / "runs" / str(args.run_id)
    return Path("logs") / "runs"


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _format_eta(seconds: float | None) -> str:
    if seconds is None:
        return "N/A"
    value = max(0, int(seconds))
    hh = value // 3600
    mm = (value % 3600) // 60
    ss = value % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def _gauge(title: str, value: float, max_value: float = 100.0) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(value),
            title={"text": title},
            gauge={"axis": {"range": [0, max_value]}},
        )
    )
    fig.update_layout(height=260, margin={"t": 40, "b": 20, "l": 20, "r": 20})
    return fig


def _line(title: str, x: list[str], y_series: list[tuple[str, list[float]]]) -> go.Figure:
    fig = go.Figure()
    for name, values in y_series:
        fig.add_trace(go.Scatter(x=x, y=values, mode="lines+markers", name=name))
    fig.update_layout(
        title=title,
        height=320,
        margin={"t": 60, "b": 30, "l": 30, "r": 20},
        legend={"orientation": "h"},
    )
    return fig


def main() -> None:
    args = _parse_args()
    run_dir = _resolve_run_dir(args)
    st.set_page_config(page_title="OpsExtract Dashboard", layout="wide")
    st.title("OpsExtract Runtime Dashboard")
    st.caption(f"run_dir: {run_dir}")
    if hasattr(st, "autorefresh"):
        st.autorefresh(interval=1000, key="ops_extract_dashboard_refresh")

    telemetry = _load_jsonl(run_dir / "telemetry.jsonl")
    progress = _load_jsonl(run_dir / "progress.jsonl")

    if not telemetry and not progress:
        st.warning("telemetry/progress data not found yet")
        return

    latest_tel = telemetry[-1] if telemetry else {}
    latest_prog = progress[-1] if progress else {}

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.plotly_chart(
            _gauge("Crash Risk %", float(latest_tel.get("crash_risk_percent", 0.0))),
            use_container_width=True,
        )
    with col_b:
        st.plotly_chart(
            _gauge("Overall Progress %", float(latest_prog.get("overall_progress_percent", 0.0))),
            use_container_width=True,
        )
    with col_c:
        st.plotly_chart(
            _gauge("Stage Progress %", float(latest_prog.get("stage_progress_percent", 0.0))),
            use_container_width=True,
        )

    col_eta1, col_eta2 = st.columns(2)
    with col_eta1:
        st.metric("ETA", _format_eta(latest_prog.get("eta_seconds")))
    with col_eta2:
        st.metric(
            "ETA Confidence %", f"{float(latest_prog.get('eta_confidence_percent', 0.0)):.1f}"
        )

    if telemetry:
        tx = [str(row.get("ts_iso", "")) for row in telemetry]
        sent_mb = [
            float(row.get("net_sent_bytes_total", 0)) / (1024.0 * 1024.0) for row in telemetry
        ]
        recv_mb = [
            float(row.get("net_recv_bytes_total", 0)) / (1024.0 * 1024.0) for row in telemetry
        ]
        sent_kbps = [float(row.get("net_sent_bps", 0)) / 1024.0 for row in telemetry]
        recv_kbps = [float(row.get("net_recv_bps", 0)) / 1024.0 for row in telemetry]
        rss_mb = [float(row.get("rss_mb", 0)) for row in telemetry]
        cpu = [float(row.get("cpu_percent", 0)) for row in telemetry]

        st.plotly_chart(
            _line("Network Cumulative (MB)", tx, [("sent_mb", sent_mb), ("recv_mb", recv_mb)]),
            use_container_width=True,
        )
        st.plotly_chart(
            _line(
                "Network Throughput (KB/s)",
                tx,
                [("sent_kbps", sent_kbps), ("recv_kbps", recv_kbps)],
            ),
            use_container_width=True,
        )
        st.plotly_chart(
            _line("Memory/CPU", tx, [("rss_mb", rss_mb), ("cpu_percent", cpu)]),
            use_container_width=True,
        )

    if progress:
        px = [str(row.get("ts_iso", "")) for row in progress]
        overall = [float(row.get("overall_progress_percent", 0)) for row in progress]
        stage = [float(row.get("stage_progress_percent", 0)) for row in progress]
        st.plotly_chart(
            _line("Progress Timeline", px, [("overall_%", overall), ("stage_%", stage)]),
            use_container_width=True,
        )

        # stage timeline (simple bar of latest stage max progress)
        stage_latest: dict[str, float] = {}
        for row in progress:
            stage_name = str(row.get("stage", ""))
            stage_latest[stage_name] = max(
                stage_latest.get(stage_name, 0.0), float(row.get("stage_progress_percent", 0))
            )
        fig = go.Figure(
            go.Bar(
                x=list(stage_latest.keys()),
                y=list(stage_latest.values()),
                marker_color="#4c78a8",
            )
        )
        fig.update_layout(title="Stage Progress Snapshot", yaxis={"range": [0, 100]}, height=320)
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
