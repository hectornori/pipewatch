"""Format per-pipeline metrics into a human-readable table."""
from __future__ import annotations

from typing import List, Optional

from pipewatch.metric_collector import MetricCollector


_HEADER = ("Pipeline", "Runs", "Avg Duration (s)", "Last Status")
_COL_W = (28, 6, 18, 12)


def _separator() -> str:
    return "+" + "+".join("-" * (w + 2) for w in _COL_W) + "+"


def _row(*cells: str) -> str:
    parts = [
        f" {str(c).ljust(w)} " for c, w in zip(cells, _COL_W)
    ]
    return "|" + "|".join(parts) + "|"


def build_metric_table(collector: MetricCollector, pipelines: List[str]) -> str:
    if not pipelines:
        return "No pipelines to report."

    lines = [
        _separator(),
        _row(*_HEADER),
        _separator(),
    ]

    for name in sorted(pipelines):
        recent = collector.get_recent(name, limit=20)
        runs = len(recent)
        avg_dur = collector.average_duration(name, limit=20)
        avg_str = f"{avg_dur:.2f}" if avg_dur is not None else "—"
        if runs == 0:
            last_status = "—"
        else:
            last_status = "OK" if recent[0].success else "FAIL"
        lines.append(_row(name, str(runs), avg_str, last_status))

    lines.append(_separator())
    return "\n".join(lines)
