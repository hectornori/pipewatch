"""Tests for SpikeNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.spike_notifier import SpikeNotifier


@dataclass
class _FakeResult:
    pipeline_name: str
    duration_seconds: float | None = None
    success: bool = True


@pytest.fixture()
def collector():
    m = MagicMock()
    m.average_duration.return_value = None
    return m


@pytest.fixture()
def inner():
    m = MagicMock()
    return m


@pytest.fixture()
def notifier(inner, collector):
    return SpikeNotifier(inner=inner, collector=collector, multiplier=2.0, min_samples=3)


@pytest.fixture()
def result():
    return _FakeResult(pipeline_name="etl_daily", duration_seconds=10.0)


def test_invalid_multiplier_raises(inner, collector):
    with pytest.raises(ValueError, match="multiplier"):
        SpikeNotifier(inner=inner, collector=collector, multiplier=0.9)


def test_invalid_min_samples_raises(inner, collector):
    with pytest.raises(ValueError, match="min_samples"):
        SpikeNotifier(inner=inner, collector=collector, min_samples=0)


def test_forwards_when_no_history(notifier, inner, collector, result):
    collector.average_duration.return_value = None
    notifier.send(result)
    inner.send.assert_called_once_with(result)
    assert notifier.forwarded == 1
    assert notifier.suppressed == 0


def test_forwards_when_spike_detected(notifier, inner, collector, result):
    collector.average_duration.return_value = 4.0  # 10 >= 4 * 2.0 = 8.0
    notifier.send(result)
    inner.send.assert_called_once_with(result)
    assert notifier.forwarded == 1


def test_suppresses_when_no_spike(notifier, inner, collector, result):
    collector.average_duration.return_value = 6.0  # 10 < 6 * 2.0 = 12.0
    notifier.send(result)
    inner.send.assert_not_called()
    assert notifier.suppressed == 1
    assert notifier.forwarded == 0


def test_forwards_when_no_pipeline_name(notifier, inner, collector):
    r = _FakeResult(pipeline_name=None, duration_seconds=10.0)  # type: ignore[arg-type]
    notifier.send(r)
    inner.send.assert_called_once_with(r)


def test_forwards_when_no_duration(notifier, inner, collector):
    r = _FakeResult(pipeline_name="etl", duration_seconds=None)
    notifier.send(r)
    inner.send.assert_called_once_with(r)


def test_collector_called_with_correct_args(notifier, inner, collector, result):
    collector.average_duration.return_value = 3.0
    notifier.send(result)
    collector.average_duration.assert_called_once_with("etl_daily", limit=3)


def test_boundary_exactly_at_threshold_forwards(notifier, inner, collector):
    r = _FakeResult(pipeline_name="pipe", duration_seconds=8.0)
    collector.average_duration.return_value = 4.0  # 8 >= 4 * 2.0 exactly
    notifier.send(r)
    inner.send.assert_called_once_with(r)
