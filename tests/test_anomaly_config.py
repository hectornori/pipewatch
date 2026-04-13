"""Tests for AnomalyConfig and anomaly_config_from_dict."""
from __future__ import annotations

import pytest

from pipewatch.anomaly_config import AnomalyConfig, anomaly_config_from_dict


def test_default_config():
    cfg = AnomalyConfig()
    assert cfg.z_threshold == 3.0
    assert cfg.min_samples == 5
    assert cfg.lookback == 50
    assert cfg.enabled is True


def test_invalid_z_threshold_raises():
    with pytest.raises(ValueError, match="z_threshold"):
        AnomalyConfig(z_threshold=-1.0)


def test_invalid_min_samples_raises():
    with pytest.raises(ValueError, match="min_samples"):
        AnomalyConfig(min_samples=1)


def test_lookback_less_than_min_samples_raises():
    with pytest.raises(ValueError, match="lookback"):
        AnomalyConfig(min_samples=10, lookback=5)


def test_from_dict_defaults():
    cfg = anomaly_config_from_dict({})
    assert cfg.z_threshold == 3.0
    assert cfg.min_samples == 5
    assert cfg.lookback == 50
    assert cfg.enabled is True


def test_from_dict_custom_values():
    cfg = anomaly_config_from_dict(
        {"z_threshold": 2.5, "min_samples": 8, "lookback": 30, "enabled": False}
    )
    assert cfg.z_threshold == pytest.approx(2.5)
    assert cfg.min_samples == 8
    assert cfg.lookback == 30
    assert cfg.enabled is False


def test_from_dict_partial_override():
    cfg = anomaly_config_from_dict({"z_threshold": 4.0})
    assert cfg.z_threshold == pytest.approx(4.0)
    assert cfg.min_samples == 5
