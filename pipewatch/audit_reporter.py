"""Format audit log entries into human-readable tables for the CLI."""
from __future__ import annotations

from typing import List

from pipewatch.audit_log import AuditEntry

_COL_WIDTHS = {
    "id": 6,
    "ts": 26,
    "event_type": 12,
    "pipeline": 24,
    "detail": 48,
}


def _truncate(value: str, width: int) -> str:
    if len(value) > width:
        return value[: width - 1] + "…"
    return value.ljust(width)


def _header() -> str:
    parts = [
        _truncate("ID", _COL_WIDTHS["id"]),
        _truncate("Timestamp", _COL_WIDTHS["ts"]),
        _truncate("Event", _COL_WIDTHS["event_type"]),
        _truncate("Pipeline", _COL_WIDTHS["pipeline"]),
        _truncate("Detail", _COL_WIDTHS["detail"]),
    ]
    row = "  ".join(parts)
    sep = "-" * len(row)
    return f"{row}\n{sep}"


def format_audit_table(entries: List[AuditEntry]) -> str:
    if not entries:
        return "No audit entries found."

    lines = [_header()]
    for e in entries:
        parts = [
            _truncate(str(e.id), _COL_WIDTHS["id"]),
            _truncate(e.ts.isoformat(timespec="seconds"), _COL_WIDTHS["ts"]),
            _truncate(e.event_type, _COL_WIDTHS["event_type"]),
            _truncate(e.pipeline_name, _COL_WIDTHS["pipeline"]),
            _truncate(e.detail, _COL_WIDTHS["detail"]),
        ]
        lines.append("  ".join(parts))
    return "\n".join(lines)
