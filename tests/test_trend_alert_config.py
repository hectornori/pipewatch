"""Tests for TrendAlertConfig and wrap_with_trend_alert."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from pipewatch.trend_alert_config import (
    TrendAlertConfig,
    trend_alert_config_from_dict,
    wrap_with_trend_alert,
)
from pipewatch.notifiers.trend_alert_notifier import TrendAlertNotifier


def test_default_config_creates_successfully():
    cfg = TrendAlertConfig()
    assert cfg.failure_rate_threshold == 0.5
    assert cfg.lookback == 10
    assert cfg.db_path == "pipewatch.db"


def test_invalid_threshold_raises():
    with pytest.raises(ValueError, match="failure_rate_threshold"):
        TrendAlertConfig(failure_rate_threshold=1.1)


def test_negative_threshold_raises():
    with pytest.raises(ValueError, match="failure_rate_threshold"):
        TrendAlertConfig(failure_rate_threshold=-0.1)


def test_invalid_lookback_raises():
    with pytest.raises(ValueError, match="lookback"):
        TrendAlertConfig(lookback=0)


def test_from_dict_defaults():
    cfg = trend_alert_config_from_dict({})
    assert cfg.failure_rate_threshold == 0.5
    assert cfg.lookback == 10


def test_from_dict_custom_values():
    cfg = trend_alert_config_from_dict(
        {"failure_rate_threshold": 0.75, "lookback": 5, "db_path": "/tmp/x.db"}
    )
    assert cfg.failure_rate_threshold == 0.75
    assert cfg.lookback == 5
    assert cfg.db_path == "/tmp/x.db"


def test_wrap_with_trend_alert_returns_notifier(tmp_path):
    cfg = TrendAlertConfig(db_path=str(tmp_path / "m.db"))
    inner = MagicMock()
    notifier = wrap_with_trend_alert(inner, cfg)
    assert isinstance(notifier, TrendAlertNotifier)
    assert notifier.failure_rate_threshold == cfg.failure_rate_threshold
    assert notifier.lookback == cfg.lookback


def test_wrap_accepts_external_collector(tmp_path):
    from pipewatch.metric_collector import MetricCollector
    cfg = TrendAlertConfig(db_path=str(tmp_path / "m.db"))
    collector = MetricCollector(db_path=str(tmp_path / "custom.db"))
    inner = MagicMock()
    notifier = wrap_with_trend_alert(inner, cfg, collector=collector)
    assert notifier.collector is collector
