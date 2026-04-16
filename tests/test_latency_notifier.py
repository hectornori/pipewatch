"""Tests for LatencyNotifier."""
from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import List

from pipewatch.notifiers.latency_notifier import LatencyNotifier


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe"
    success: bool = True
    duration_seconds: float | None = None


@dataclass
class _FakeNotifier:
    received: List = field(default_factory=list)

    def send(self, result) -> None:
        self.received.append(result)


@pytest.fixture
def inner():
    return _FakeNotifier()


@pytest.fixture
def notifier(inner):
    return LatencyNotifier(inner=inner, threshold_seconds=5.0)


@pytest.fixture
def result():
    return _FakeResult()


def test_invalid_threshold_zero_raises():
    with pytest.raises(ValueError):
        LatencyNotifier(inner=_FakeNotifier(), threshold_seconds=0)


def test_invalid_threshold_negative_raises():
    with pytest.raises(ValueError):
        LatencyNotifier(inner=_FakeNotifier(), threshold_seconds=-1.0)


def test_forwards_when_no_duration(notifier, inner, result):
    result.duration_seconds = None
    notifier.send(result)
    assert len(inner.received) == 1


def test_forwards_when_duration_exceeds_threshold(notifier, inner, result):
    result.duration_seconds = 10.0
    notifier.send(result)
    assert len(inner.received) == 1
    assert notifier.sent_count == 1


def test_suppresses_when_duration_at_threshold(notifier, inner, result):
    result.duration_seconds = 5.0
    notifier.send(result)
    assert len(inner.received) == 0
    assert notifier.suppressed_count == 1


def test_suppresses_when_duration_below_threshold(notifier, inner, result):
    result.duration_seconds = 2.5
    notifier.send(result)
    assert len(inner.received) == 0


def test_counts_track_correctly(notifier, inner):
    notifier.send(_FakeResult(duration_seconds=1.0))
    notifier.send(_FakeResult(duration_seconds=1.0))
    notifier.send(_FakeResult(duration_seconds=9.0))
    assert notifier.suppressed_count == 2
    assert notifier.sent_count == 1


def test_result_without_duration_attr_forwards(notifier, inner):
    class Bare:
        pipeline_name = "bare"
    notifier.send(Bare())
    assert len(inner.received) == 1
