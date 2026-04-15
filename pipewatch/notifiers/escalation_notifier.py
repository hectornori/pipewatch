"""Notifier that escalates to a secondary notifier after repeated failures."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pipewatch.escalation import EscalationPolicy
from pipewatch.monitor import CheckResult


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class EscalationNotifier:
    """Wraps a primary notifier and escalates to a secondary when the
    escalation policy threshold is met.

    The primary notifier always receives the result.  When
    ``policy.should_escalate()`` returns ``True`` the escalation notifier
    is also invoked.
    """

    def __init__(
        self,
        primary: Notifier,
        escalation: Notifier,
        policy: EscalationPolicy,
    ) -> None:
        self._primary = primary
        self._escalation = escalation
        self._policy = policy

    def send(self, result: CheckResult) -> None:
        """Forward *result* to the primary notifier and optionally escalate."""
        self._primary.send(result)

        if not result.passed:
            self._policy.record(result)
            if self._policy.should_escalate(result):
                self._escalation.send(result)
