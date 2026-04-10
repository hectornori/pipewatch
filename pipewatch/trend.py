"""Trend analysis for pipeline check results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.monitor import CheckResult


@dataclass
class TrendSummary:
    pipeline_name: str
    window: int  # number of recent checks considered
    total: int
    failures: int
    consecutive_failures: int
    is_degrading: bool  # failure rate increased in second half vs first half

    @property
    def failure_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.failures / self.total


def analyse(pipeline_name: str, results: List[CheckResult], window: int = 10) -> TrendSummary:
    """Analyse a list of recent CheckResults and return a TrendSummary.

    Args:
        pipeline_name: Name of the pipeline being analysed.
        results: Ordered list of results, oldest first.
        window: Maximum number of results to consider.
    """
    recent = results[-window:] if len(results) > window else results
    total = len(recent)
    failures = sum(1 for r in recent if not r.success)

    # Count trailing consecutive failures (most-recent streak)
    consecutive_failures = 0
    for r in reversed(recent):
        if not r.success:
            consecutive_failures += 1
        else:
            break

    # Degradation: compare failure rate in first half vs second half
    is_degrading = False
    if total >= 4:
        mid = total // 2
        first_half = recent[:mid]
        second_half = recent[mid:]
        first_rate = sum(1 for r in first_half if not r.success) / len(first_half)
        second_rate = sum(1 for r in second_half if not r.success) / len(second_half)
        is_degrading = second_rate > first_rate

    return TrendSummary(
        pipeline_name=pipeline_name,
        window=window,
        total=total,
        failures=failures,
        consecutive_failures=consecutive_failures,
        is_degrading=is_degrading,
    )


def format_trend(summary: TrendSummary) -> str:
    """Return a human-readable one-line trend description."""
    rate_pct = summary.failure_rate * 100
    degrading_label = " [DEGRADING]" if summary.is_degrading else ""
    return (
        f"{summary.pipeline_name}: {summary.failures}/{summary.total} failures "
        f"({rate_pct:.0f}%), {summary.consecutive_failures} consecutive{degrading_label}"
    )
