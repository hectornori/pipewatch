"""Render a health-score table for CLI output."""
from __future__ import annotations

from typing import List

from pipewatch.pipeline_health import HealthScore

_COL_NAME = 30
_COL_GRADE = 6
_COL_SCORE = 8
_COL_PASS = 7
_COL_FAIL = 7
_COL_CONSEC = 10


def _header() -> str:
    return (
        f"{'Pipeline':<{_COL_NAME}}"
        f"{'Grade':<{_COL_GRADE}}"
        f"{'Score':>{_COL_SCORE}}"
        f"{'Passed':>{_COL_PASS}}"
        f"{'Failed':>{_COL_FAIL}}"
        f"{'Consec.Fail':>{_COL_CONSEC}}"
    )


def _separator() -> str:
    return "-" * (_COL_NAME + _COL_GRADE + _COL_SCORE + _COL_PASS + _COL_FAIL + _COL_CONSEC)


def _row(hs: HealthScore) -> str:
    name = hs.pipeline_name[:_COL_NAME - 1].ljust(_COL_NAME)
    return (
        f"{name}"
        f"{hs.grade:<{_COL_GRADE}}"
        f"{hs.score:>{_COL_SCORE}.2%}"
        f"{hs.passed:>{_COL_PASS}}"
        f"{hs.failed:>{_COL_FAIL}}"
        f"{hs.consecutive_failures:>{_COL_CONSEC}}"
    )


def build_health_table(scores: List[HealthScore]) -> str:
    """Return a formatted plain-text health table."""
    if not scores:
        return "No pipeline health data available."

    lines = [_header(), _separator()]
    for hs in sorted(scores, key=lambda h: h.score):
        lines.append(_row(hs))
    lines.append(_separator())
    return "\n".join(lines)
