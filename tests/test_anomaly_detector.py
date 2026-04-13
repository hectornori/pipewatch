"""Tests for AnomalyDetector and AnomalyResult."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from pipewatch.anomaly_detector import AnomalyDetector, _mean, _stddev
from pipewatch.metric_collector import MetricCollector, PipelineMetric


UTC = timezone.utc


@pytest.fixture
def collector():
    conn = sqlite3.connect(":memory:")
    return MetricCollector(db_path=":memory:", _conn=conn)


@pytest.fixture
def detector(collector):
    return AnomalyDetector(collector, z_threshold=2.0, min_samples=3, lookback=20)


def _metric(name: str, duration: float, success: bool = True) -> PipelineMetric:
    return PipelineMetric(
        pipeline_name=name,
        success=success,
        duration_seconds=duration,
        recorded_at=datetime.now(UTC),
    )


def test_mean_basic():
    assert _mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)


def test_stddev_basic():
    values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    mean = _mean(values)
    assert _stddev(values, mean) == pytest.approx(2.0)


def test_not_anomalous_below_threshold(detector, collector):
    for d in [1.0, 1.1, 1.0, 0.9, 1.05]:
        collector.record(_metric("pipe", d))
    result = detector.check("pipe", 1.2)
    assert not result.is_anomalous


def test_anomalous_above_threshold(detector, collector):
    for d in [1.0, 1.0, 1.0, 1.0, 1.0]:
        collector.record(_metric("pipe", d))
    result = detector.check("pipe", 100.0)
    assert result.is_anomalous
    assert result.reason is not None
    assert result.z_score is not None and result.z_score > 2.0


def test_insufficient_samples_returns_not_anomalous(detector, collector):
    collector.record(_metric("pipe", 1.0))
    result = detector.check("pipe", 999.0)
    assert not result.is_anomalous


def test_zero_stddev_returns_not_anomalous(detector, collector):
    for _ in range(5):
        collector.record(_metric("pipe", 5.0))
    result = detector.check("pipe", 5.0)
    assert not result.is_anomalous


def test_invalid_z_threshold_raises():
    with pytest.raises(ValueError, match="z_threshold"):
        AnomalyDetector(MagicMock(), z_threshold=0)


def test_invalid_min_samples_raises():
    with pytest.raises(ValueError, match="min_samples"):
        AnomalyDetector(MagicMock(), min_samples=1)


def test_check_all_skips_none_duration(detector, collector):
    for d in [1.0, 1.0, 1.0, 1.0, 1.0]:
        collector.record(_metric("pipe", d))
    metrics = [
        _metric("pipe", 100.0),
        PipelineMetric(
            pipeline_name="pipe",
            success=False,
            duration_seconds=None,
            recorded_at=datetime.now(UTC),
        ),
    ]
    results = detector.check_all(metrics)
    assert len(results) == 1
    assert results[0].is_anomalous


def test_bool_false_for_normal(detector, collector):
    for d in [1.0, 1.0, 1.0, 1.0, 1.0]:
        collector.record(_metric("pipe", d))
    result = detector.check("pipe", 1.0)
    assert not bool(result)
