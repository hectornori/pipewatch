"""Tests for NoiseFilterNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.notifiers.noise_filter_notifier import NoiseFilterNotifier


@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool
    error_message: str | None = None


@dataclass
class _FakeNotifier:
    received: List[_FakeResult] = field(default_factory=list)

    def send(self, result) -> None:
        self.received.append(result)


@pytest.fixture
def inner():
    return _FakeNotifier()


@pytest.fixture
def notifier(inner):
    return NoiseFilterNotifier(inner=inner, min_failures=3)


def _fail(name: str = "pipe") -> _FakeResult:
    return _FakeResult(pipeline_name=name, success=False, error_message="boom")


def _ok(name: str = "pipe") -> _FakeResult:
    return _FakeResult(pipeline_name=name, success=True)


def test_invalid_min_failures_raises():
    with pytest.raises(ValueError):
        NoiseFilterNotifier(inner=_FakeNotifier(), min_failures=0)


def test_no_dispatch_below_threshold(notifier, inner):
    notifier.send(_fail())
    notifier.send(_fail())
    assert len(inner.received) == 0


def test_dispatch_at_threshold(notifier, inner):
    for _ in range(3):
        notifier.send(_fail())
    assert len(inner.received) == 1


def test_dispatch_continues_above_threshold(notifier, inner):
    for _ in range(5):
        notifier.send(_fail())
    assert len(inner.received) == 3


def test_success_resets_counter(notifier, inner):
    notifier.send(_fail())
    notifier.send(_fail())
    notifier.send(_ok())
    # counter reset; two more failures still below threshold
    notifier.send(_fail())
    notifier.send(_fail())
    assert len(inner.received) == 0


def test_success_not_forwarded(notifier, inner):
    notifier.send(_ok())
    assert len(inner.received) == 0


def test_counters_isolated_per_pipeline(notifier, inner):
    notifier.send(_fail("a"))
    notifier.send(_fail("b"))
    # neither pipeline has reached threshold of 3
    assert len(inner.received) == 0


def test_manual_reset(notifier, inner):
    notifier.send(_fail())
    notifier.send(_fail())
    notifier.reset("pipe")
    notifier.send(_fail())
    notifier.send(_fail())
    # after reset only 2 failures, still below threshold
    assert len(inner.received) == 0


def test_counts_property(notifier):
    notifier.send(_fail())
    notifier.send(_fail())
    assert notifier.counts["pipe"] == 2
