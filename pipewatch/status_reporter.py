"""Formats a human-readable status table from SnapshotStore for the CLI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from pipewatch.snapshot import PipelineSnapshot, SnapshotStore

_OK_ICON = "\u2705"
_FAIL_ICON = "\u274c"
_UNKNOWN_ICON = "\u2753"


@dataclass
class StatusRow:
    name: str
    icon: str
    status: str
    last_checked: str
    last_error: str


def _format_snapshot(snap: PipelineSnapshot) -> StatusRow:
    icon = _OK_ICON if snap.status == "ok" else _FAIL_ICON
    return StatusRow(
        name=snap.pipeline_name,
        icon=icon,
        status=snap.status.upper(),
        last_checked=snap.last_checked.strftime("%Y-%m-%d %H:%M:%S"),
        last_error=snap.last_error or "-",
    )


def build_status_table(store: SnapshotStore, pipeline_names: List[str]) -> str:
    """Return a formatted status table string for *pipeline_names*.

    Pipelines with no snapshot are shown as UNKNOWN.
    """
    rows: list[StatusRow] = []
    for name in pipeline_names:
        snap = store.get(name)
        if snap is None:
            rows.append(
                StatusRow(
                    name=name,
                    icon=_UNKNOWN_ICON,
                    status="UNKNOWN",
                    last_checked="-",
                    last_error="-",
                )
            )
        else:
            rows.append(_format_snapshot(snap))

    col_w = max((len(r.name) for r in rows), default=8)
    header = f"{'Pipeline':<{col_w}}  {'':2}  {'Status':<8}  {'Last Checked':<19}  Error"
    separator = "-" * len(header)
    lines = [header, separator]
    for r in rows:
        lines.append(
            f"{r.name:<{col_w}}  {r.icon}  {r.status:<8}  {r.last_checked:<19}  {r.last_error}"
        )
    return "\n".join(lines)
