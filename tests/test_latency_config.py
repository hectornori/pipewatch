"""Tests for LatencyConfig."""
from __future__ import annotations

import pytest
from pipewatch.latency_config import LatencyConfig, latency_config_from_dict, wrap_with_latency


def test_valid_config_creates_successfully():
    cfg = LatencyConfig(threshold_seconds=10.0)
    assert cfg.threshold_seconds == 10.0
    assert cfg.db_path == "pipewatch_latency.db"


def test_zero_threshold_raises():
    with pytest.raises(ValueError):
        LatencyConfig(threshold_seconds=0)


def test_negative_threshold_raises():
    with pytest.raises(ValueError):
        LatencyConfig(threshold_seconds=-5.0)


def test_from_dict_minimal():
    cfg = latency_config_from_dict({"threshold_seconds": "30"})
    assert cfg.threshold_seconds == 30.0
    assert cfg.db_path == "pipewatch_latency.db"


def test_from_dict_with_db_path():
    cfg = latency_config_from_dict({"threshold_seconds": 15.0, "db_path": "/tmp/lat.db"})
    assert cfg.db_path == "/tmp/lat.db"


def test_from_dict_missing_threshold_raises():
    with pytest.raises(KeyError):
        latency_config_from_dict({})


def test_wrap_with_latency_returns_latency_notifier():
    from pipewatch.notifiers.latency_notifier import LatencyNotifier
    from dataclasses import dataclass

    @dataclass
    class _Fake:
        def send(self, r): pass

    cfg = LatencyConfig(threshold_seconds=5.0)
    wrapped = wrap_with_latency(_Fake(), cfg)
    assert isinstance(wrapped, LatencyNotifier)
    assert wrapped.threshold_seconds == 5.0
