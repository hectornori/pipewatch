"""Tests for TrendAlertNotifier."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass
from datetime import datetime, timezone

from pipewatch.notifiers.trend_alert_notifier import TrendAlertNotifier
from pipewatch.metric_collector import MetricCollector, PipelineMetric


@dataclass
class _FakeResult:
    pipeline: str
    success: bool
    error_message: str | None = None
    duration_seconds: float = 1.0


@pytest.fixture()
def collector(tmp_path):
    return MetricCollector(db_path=str(tmp_path / "metrics.db"))


@pytest.fixture()
def inner():
    m = MagicMock()
    m.send = MagicMock()
    return m


def _record(collector: MetricCollector, pipeline: str, success: bool) -> None:
    collector.record(
        PipelineMetric(
            pipeline=pipeline,
            success=success,
            duration_seconds=1.0,
            checked_at=datetime.now(timezone.utc),
        )
    )


def test_send_forwards_when_failure_rate_at_threshold(collector, inner):
    notifier = TrendAlertNotifier(inner=inner, collector=collector, failure_rate_threshold=0.5, lookback=4)
    for _ in range(2):
        _record(collector, "pipe", success=False)
    for _ in range(2):
        _record(collector, "pipe", success=True)
    notifier.send(_FakeResult(pipeline="pipe", success=False))
    inner.send.assert_called_once()


def test_send_suppressed_when_failure_rate_below_threshold(collector, inner):
    notifier = TrendAlertNotifier(inner=inner, collector=collector, failure_rate_threshold=0.8, lookback=4)
    _record(collector, "pipe", success=False)
    for _ in range(3):
        _record(collector, "pipe", success=True)
    notifier.send(_FakeResult(pipeline="pipe", success=False))
    inner.send.assert_not_called()


def test_send_forwards_when_all_failures(collector, inner):
    notifier = TrendAlertNotifier(inner=inner, collector=collector, failure_rate_threshold=0.5, lookback=3)
    for _ in range(3):
        _record(collector, "pipe", success=False)
    notifier.send(_FakeResult(pipeline="pipe", success=False))
    inner.send.assert_called_once()


def test_sent_count_increments(collector, inner):
    notifier = TrendAlertNotifier(inner=inner, collector=collector, failure_rate_threshold=0.0, lookback=2)
    notifier.send(_FakeResult(pipeline="pipe", success=False))
    notifier.send(_FakeResult(pipeline="pipe", success=False))
    assert notifier.sent_count == 2


def test_no_pipeline_attribute_forwards_unconditionally(inner, collector):
    notifier = TrendAlertNotifier(inner=inner, collector=collector, failure_rate_threshold=0.99)
    notifier.send(object())
    inner.send.assert_called_once()


def test_invalid_threshold_raises():
    with pytest.raises(ValueError, match="failure_rate_threshold"):
        TrendAlertNotifier(inner=MagicMock(), collector=MagicMock(), failure_rate_threshold=1.5)


def test_invalid_lookback_raises():
    with pytest.raises(ValueError, match="lookback"):
        TrendAlertNotifier(inner=MagicMock(), collector=MagicMock(), lookback=0)
