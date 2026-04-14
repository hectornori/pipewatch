"""Tests for BackoffConfig and helpers."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.backoff_config import (
    BackoffConfig,
    backoff_config_from_dict,
    wrap_with_backoff,
)
from pipewatch.notifiers.backoff_notifier import BackoffNotifier


def test_default_config_creates_successfully():
    cfg = BackoffConfig()
    assert cfg.base_delay == 1.0
    assert cfg.max_delay == 60.0
    assert cfg.multiplier == 2.0


def test_invalid_base_delay_raises():
    with pytest.raises(ValueError, match="base_delay"):
        BackoffConfig(base_delay=0.0)


def test_invalid_max_delay_raises():
    with pytest.raises(ValueError, match="max_delay"):
        BackoffConfig(base_delay=10.0, max_delay=5.0)


def test_invalid_multiplier_raises():
    with pytest.raises(ValueError, match="multiplier"):
        BackoffConfig(multiplier=0.9)


def test_from_dict_defaults():
    cfg = backoff_config_from_dict({})
    assert cfg.base_delay == 1.0
    assert cfg.max_delay == 60.0
    assert cfg.multiplier == 2.0


def test_from_dict_custom_values():
    cfg = backoff_config_from_dict({"base_delay": 2.0, "max_delay": 30.0, "multiplier": 3.0})
    assert cfg.base_delay == 2.0
    assert cfg.max_delay == 30.0
    assert cfg.multiplier == 3.0


def test_from_dict_coerces_strings():
    cfg = backoff_config_from_dict({"base_delay": "0.5", "max_delay": "10", "multiplier": "1.5"})
    assert cfg.base_delay == 0.5
    assert cfg.max_delay == 10.0
    assert cfg.multiplier == 1.5


def test_wrap_with_backoff_returns_backoff_notifier():
    inner = MagicMock()
    wrapped = wrap_with_backoff(inner, {"base_delay": 0.1, "max_delay": 5.0, "multiplier": 2.0})
    assert isinstance(wrapped, BackoffNotifier)
    assert wrapped.inner is inner
    assert wrapped.base_delay == 0.1
    assert wrapped.max_delay == 5.0
    assert wrapped.multiplier == 2.0


def test_wrap_with_backoff_defaults():
    inner = MagicMock()
    wrapped = wrap_with_backoff(inner, {})
    assert wrapped.base_delay == 1.0
    assert wrapped.max_delay == 60.0
