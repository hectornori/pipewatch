"""Digest report generation for pipeline check summaries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from pipewatch.monitor import CheckResult


@dataclass
class DigestReport:
    """Summary of pipeline check results for a reporting period."""

    generated_at: datetime = field(default_factory=datetime.utcnow)
    results: List[CheckResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def failure_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.failed / self.total

    def failed_results(self) -> List[CheckResult]:
        return [r for r in self.results if not r.success]

    def to_text(self) -> str:
        """Render the digest as a human-readable text block."""
        lines = [
            f"PipeWatch Digest — {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"Pipelines checked : {self.total}",
            f"Passed            : {self.passed}",
            f"Failed            : {self.failed}",
            f"Failure rate      : {self.failure_rate:.0%}",
        ]
        if self.failed_results():
            lines.append("\nFailed pipelines:")
            for r in self.failed_results():
                err = r.error_message or "unknown error"
                lines.append(f"  • {r.pipeline_name}: {err}")
        return "\n".join(lines)


def build_digest(results: List[CheckResult]) -> DigestReport:
    """Construct a DigestReport from a list of CheckResult objects."""
    return DigestReport(results=list(results))
