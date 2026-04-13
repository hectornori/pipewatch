"""Formats dead-letter entries as a human-readable table."""
from __future__ import annotations

from pipewatch.notifiers.dead_letter_notifier import DeadLetterStore

_HEADER = f"{'ID':<6} {'Pipeline':<24} {'Error':<40} {'Recorded At'}"
_SEP = "-" * len(_HEADER)
_TRUNC = 38


def _truncate(text: str, max_len: int = _TRUNC) -> str:
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def build_dead_letter_table(store: DeadLetterStore) -> str:
    entries = store.get_all()
    if not entries:
        return "No dead-letter entries."

    lines = [_HEADER, _SEP]
    for e in entries:
        recorded = e.recorded_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(
            f"{e.id:<6} {_truncate(e.pipeline, 24):<24} {_truncate(e.error, 40):<40} {recorded}"
        )
    return "\n".join(lines)
