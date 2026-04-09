"""Alert rule evaluation for pipeline check results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.monitor import CheckResult


@dataclass
class AlertRule:
    """Defines conditions under which an alert should be fired."""
    name: str
    consecutive_failures: int = 1
    failure_rate_threshold: Optional[float] = None  # 0.0–1.0
    pipelines: List[str] = field(default_factory=list)  # empty = all

    def __post_init__(self) -> None:
        if self.consecutive_failures < 1:
            raise ValueError("consecutive_failures must be >= 1")
        if self.failure_rate_threshold is not None:
            if not (0.0 <= self.failure_rate_threshold <= 1.0):
                raise ValueError("failure_rate_threshold must be between 0.0 and 1.0")

    def applies_to(self, pipeline_name: str) -> bool:
        """Return True if this rule should be evaluated for the given pipeline."""
        return not self.pipelines or pipeline_name in self.pipelines

    def should_alert(self, recent_results: List[CheckResult]) -> bool:
        """Evaluate rule against a list of recent results (newest last)."""
        if not recent_results:
            return False

        # Consecutive failures check
        tail = recent_results[-self.consecutive_failures:]
        if len(tail) == self.consecutive_failures and all(not r.success for r in tail):
            return True

        # Failure rate check
        if self.failure_rate_threshold is not None:
            failures = sum(1 for r in recent_results if not r.success)
            rate = failures / len(recent_results)
            if rate >= self.failure_rate_threshold:
                return True

        return False


def rule_from_dict(data: dict) -> AlertRule:
    """Construct an AlertRule from a plain dictionary (e.g. parsed YAML)."""
    return AlertRule(
        name=data["name"],
        consecutive_failures=int(data.get("consecutive_failures", 1)),
        failure_rate_threshold=(
            float(data["failure_rate_threshold"])
            if "failure_rate_threshold" in data
            else None
        ),
        pipelines=list(data.get("pipelines", [])),
    )
