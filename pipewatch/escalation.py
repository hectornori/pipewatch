"""Escalation policy: re-notify via a secondary channel after a cooldown if a pipeline is still failing."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from pipewatch.monitor import CheckResult
from pipewatch.suppression import SuppressionStore


@dataclass
class EscalationPolicy:
    """Defines when and how to escalate an unresolved failure."""

    # Minutes to wait after the first alert before escalating
    escalate_after_minutes: int = 60
    # Maximum number of escalations to send (0 = unlimited)
    max_escalations: int = 3
    # Namespace used in the suppression store so escalations are tracked separately
    _namespace: str = field(default="escalation", init=False, repr=False)

    def __post_init__(self) -> None:
        if self.escalate_after_minutes <= 0:
            raise ValueError("escalate_after_minutes must be a positive integer")
        if self.max_escalations < 0:
            raise ValueError("max_escalations must be >= 0")

    def should_escalate(
        self,
        result: CheckResult,
        store: SuppressionStore,
        escalation_count: int,
    ) -> bool:
        """Return True when the policy decides an escalation notice should be sent."""
        if result.success:
            return False
        if self.max_escalations != 0 and escalation_count >= self.max_escalations:
            return False
        last = store.last_alerted_at(result.pipeline_name, namespace=self._namespace)
        if last is None:
            return True
        return datetime.utcnow() - last >= timedelta(minutes=self.escalate_after_minutes)

    def record(
        self,
        result: CheckResult,
        store: SuppressionStore,
    ) -> None:
        """Persist the escalation timestamp so the next call to should_escalate is correct."""
        store.record_alert(result.pipeline_name, namespace=self._namespace)


def policy_from_dict(data: dict) -> EscalationPolicy:
    """Construct an EscalationPolicy from a plain configuration dictionary."""
    return EscalationPolicy(
        escalate_after_minutes=int(data.get("escalate_after_minutes", 60)),
        max_escalations=int(data.get("max_escalations", 3)),
    )
