"""Tests for MetricCollector."""
from __future__ import annotations

import pytest

from pipewatch.metric_collector import MetricCollector
from pipewatch.monitor import CheckResult


@pytest.fixture()
def collector() -> MetricCollector:
    return MetricCollector(db_path=":memory:")


def _ok(name: str = "pipe_a") -> CheckResult:
    return CheckResult(pipeline=name, success=True, error_message=None)


def _fail(name: str = "pipe_a") -> CheckResult:
    return CheckResult(pipeline=name, success=False, error_message="boom")


def test_get_recent_empty_before_record(collector: MetricCollector) -> None:
    assert collector.get_recent("pipe_a") == []


def test_average_duration_none_before_record(collector: MetricCollector) -> None:
    assert collector.average_duration("pipe_a") is None


def test_record_success(collector: MetricCollector) -> None:
    collector.record(_ok(), duration_seconds=1.5)
    recent = collector.get_recent("pipe_a")
    assert len(recent) == 1
    assert recent[0].success is True
    assert recent[0].duration_seconds == pytest.approx(1.5)
    assert recent[0].error_message is None


def test_record_failure(collector: MetricCollector) -> None:
    collector.record(_fail(), duration_seconds=3.0)
    recent = collector.get_recent("pipe_a")
    assert len(recent) == 1
    assert recent[0].success is False
    assert recent[0].error_message == "boom"


def test_get_recent_respects_limit(collector: MetricCollector) -> None:
    for i in range(10):
        collector.record(_ok(), duration_seconds=float(i))
    assert len(collector.get_recent("pipe_a", limit=5)) == 5


def test_get_recent_returns_most_recent_first(collector: MetricCollector) -> None:
    collector.record(_ok(), duration_seconds=1.0)
    collector.record(_ok(), duration_seconds=9.0)
    recent = collector.get_recent("pipe_a", limit=2)
    assert recent[0].duration_seconds == pytest.approx(9.0)


def test_average_duration_single_entry(collector: MetricCollector) -> None:
    collector.record(_ok(), duration_seconds=4.0)
    assert collector.average_duration("pipe_a") == pytest.approx(4.0)


def test_average_duration_multiple_entries(collector: MetricCollector) -> None:
    for d in [2.0, 4.0, 6.0]:
        collector.record(_ok(), duration_seconds=d)
    assert collector.average_duration("pipe_a") == pytest.approx(4.0)


def test_records_isolated_by_pipeline(collector: MetricCollector) -> None:
    collector.record(_ok("pipe_a"), duration_seconds=1.0)
    collector.record(_ok("pipe_b"), duration_seconds=2.0)
    assert len(collector.get_recent("pipe_a")) == 1
    assert len(collector.get_recent("pipe_b")) == 1
    assert collector.average_duration("pipe_a") == pytest.approx(1.0)
    assert collector.average_duration("pipe_b") == pytest.approx(2.0)
