"""Pipeline health scoring: aggregate a numeric health score from recent results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from pipewatch.monitor import CheckResult


@dataclass
class HealthScore:
    pipeline_name: str
    score: float          # 0.0 (all failing) … 1.0 (all passing)
    total: int
    passed: int
    failed: int
    consecutive_failures: int

    @property
    def grade(self) -> str:
        if self.score >= 0.9:
            return "A"
        if self.score >= 0.75:
            return "B"
        if self.score >= 0.5:
            return "C"
        if self.score >= 0.25:
            return "D"
        return "F"

    @property
    def is_healthy(self) -> bool:
        return self.score >= 0.75


def compute_health(pipeline_name: str, results: List[CheckResult]) -> HealthScore:
    """Compute a HealthScore from a list of recent CheckResult objects."""
    if not results:
        return HealthScore(
            pipeline_name=pipeline_name,
            score=1.0,
            total=0,
            passed=0,
            failed=0,
            consecutive_failures=0,
        )

    total = len(results)
    passed = sum(1 for r in results if r.success)
    failed = total - passed
    score = passed / total

    consecutive_failures = 0
    for r in reversed(results):
        if not r.success:
            consecutive_failures += 1
        else:
            break

    return HealthScore(
        pipeline_name=pipeline_name,
        score=round(score, 4),
        total=total,
        passed=passed,
        failed=failed,
        consecutive_failures=consecutive_failures,
    )


def compute_all_health(
    results_by_pipeline: dict[str, List[CheckResult]],
) -> List[HealthScore]:
    """Return a HealthScore for every pipeline in the provided mapping."""
    return [
        compute_health(name, results)
        for name, results in results_by_pipeline.items()
    ]
