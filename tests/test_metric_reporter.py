"""Tests for metric_reporter.build_metric_table."""
from __future__ import annotations

import pytest

from pipewatch.metric_collector import MetricCollector
from pipewatch.metric_reporter import build_metric_table
from pipewatch.monitor import CheckResult


@pytest.fixture()
def collector() -> MetricCollector:
    return MetricCollector(db_path=":memory:")


def _ok(name: str) -> CheckResult:
    return CheckResult(pipeline=name, success=True, error_message=None)


def _fail(name: str) -> CheckResult:
    return CheckResult(pipeline=name, success=False, error_message="err")


def test_empty_pipelines_returns_message(collector: MetricCollector) -> None:
    table = build_metric_table(collector, [])
    assert "No pipelines" in table


def test_table_contains_pipeline_name(collector: MetricCollector) -> None:
    collector.record(_ok("my_pipeline"), duration_seconds=1.0)
    table = build_metric_table(collector, ["my_pipeline"])
    assert "my_pipeline" in table


def test_table_shows_ok_status(collector: MetricCollector) -> None:
    collector.record(_ok("pipe_a"), duration_seconds=1.0)
    table = build_metric_table(collector, ["pipe_a"])
    assert "OK" in table


def test_table_shows_fail_status(collector: MetricCollector) -> None:
    collector.record(_fail("pipe_b"), duration_seconds=2.0)
    table = build_metric_table(collector, ["pipe_b"])
    assert "FAIL" in table


def test_table_shows_avg_duration(collector: MetricCollector) -> None:
    for d in [2.0, 4.0]:
        collector.record(_ok("pipe_c"), duration_seconds=d)
    table = build_metric_table(collector, ["pipe_c"])
    assert "3.00" in table


def test_table_shows_dash_for_no_runs(collector: MetricCollector) -> None:
    table = build_metric_table(collector, ["ghost_pipe"])
    assert "—" in table


def test_table_multiple_pipelines(collector: MetricCollector) -> None:
    collector.record(_ok("alpha"), duration_seconds=1.0)
    collector.record(_fail("beta"), duration_seconds=5.0)
    table = build_metric_table(collector, ["alpha", "beta"])
    assert "alpha" in table
    assert "beta" in table
