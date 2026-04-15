"""Build a plain-text table from archived notification records."""
from __future__ import annotations

from pipewatch.notifiers.archive_notifier import ArchiveStore

_HEADER = f"{'PIPELINE':<30} {'STATUS':<8} {'ERROR':<40} {'ARCHIVED AT'}"
_SEP = "-" * len(_HEADER)


def _truncate(text: str | None, width: int) -> str:
    if text is None:
        return ""
    return text if len(text) <= width else text[: width - 1] + "…"


def build_archive_table(store: ArchiveStore, pipeline: str, limit: int = 20) -> str:
    rows = store.get_recent(pipeline, limit=limit)
    if not rows:
        return f"No archived records for pipeline '{pipeline}'."

    lines = [_HEADER, _SEP]
    for row in rows:
        status = "OK" if row["success"] else "FAIL"
        error = _truncate(row["error"], 40)
        ts = row["archived_at"]
        lines.append(f"{row['pipeline']:<30} {status:<8} {error:<40} {ts}")
    return "\n".join(lines)
