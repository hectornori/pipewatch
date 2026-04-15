"""Tests for EscalationNotifier."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

import pytest

from pipewatch.escalation import EscalationPolicy
from pipewatch.monitor import CheckResult
from pipewatch.notifiers.escalation_notifier import EscalationNotifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _FakeNotifier:
    received: List[CheckResult] = field(default_factory=list)

    def send(self, result: CheckResult) -> None:
        self.received.append(result)


def _result(passed: bool, pipeline: str = "pipe", error: str | None = None) -> CheckResult:
    return CheckResult(
        pipeline_name=pipeline,
        passed=passed,
        error_message=error,
        checked_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def primary() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def escalation_target() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def policy() -> EscalationPolicy:
    # Escalate after 2 consecutive failures, 0-minute delay so it triggers immediately.
    return EscalationPolicy(escalate_after=2, escalate_after_minutes=0)


@pytest.fixture()
def notifier(primary, escalation_target, policy) -> EscalationNotifier:
    return EscalationNotifier(
        primary=primary,
        escalation=escalation_target,
        policy=policy,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_primary_always_receives_success(notifier, primary, escalation_target):
    result = _result(passed=True)
    notifier.send(result)
    assert primary.received == [result]
    assert escalation_target.received == []


def test_primary_always_receives_failure(notifier, primary):
    result = _result(passed=False, error="boom")
    notifier.send(result)
    assert result in primary.received


def test_no_escalation_below_threshold(notifier, escalation_target):
    # Only one failure — threshold is 2, so no escalation yet.
    notifier.send(_result(passed=False, error="err"))
    assert escalation_target.received == []


def test_escalation_triggered_at_threshold(notifier, escalation_target):
    fail = _result(passed=False, error="err")
    notifier.send(fail)
    notifier.send(fail)
    # Second failure meets the threshold of 2.
    assert len(escalation_target.received) == 1


def test_escalation_triggered_on_every_failure_after_threshold(notifier, escalation_target):
    fail = _result(passed=False, error="err")
    for _ in range(4):
        notifier.send(fail)
    # Escalation should fire on failures 2, 3, 4 (3 times).
    assert len(escalation_target.received) == 3


def test_success_does_not_trigger_escalation(notifier, escalation_target):
    notifier.send(_result(passed=True))
    notifier.send(_result(passed=True))
    assert escalation_target.received == []
