"""Tests for DigestIntervalConfig."""
from __future__ import annotations

import pytest

from pipewatch.digest_interval_config import (
    DigestIntervalConfig,
    digest_interval_config_from_dict,
    wrap_with_digest_interval,
)
from pipewatch.notifiers.digest_interval_notifier import DigestIntervalNotifier


def test_default_config_creates_successfully():
    cfg = DigestIntervalConfig()
    assert cfg.interval_seconds == 300.0
    assert cfg.db_path == "pipewatch.db"


def test_zero_interval_raises():
    with pytest.raises(ValueError, match="interval_seconds must be positive"):
        DigestIntervalConfig(interval_seconds=0)


def test_negative_interval_raises():
    with pytest.raises(ValueError, match="interval_seconds must be positive"):
        DigestIntervalConfig(interval_seconds=-10)


def test_from_dict_defaults():
    cfg = digest_interval_config_from_dict({})
    assert cfg.interval_seconds == 300.0
    assert cfg.db_path == "pipewatch.db"


def test_from_dict_custom_values():
    cfg = digest_interval_config_from_dict({"interval_seconds": 120, "db_path": "/tmp/pw.db"})
    assert cfg.interval_seconds == 120.0
    assert cfg.db_path == "/tmp/pw.db"


def test_from_dict_string_interval_coerced():
    cfg = digest_interval_config_from_dict({"interval_seconds": "90"})
    assert cfg.interval_seconds == 90.0


def test_wrap_returns_digest_interval_notifier():
    from unittest.mock import MagicMock
    inner = MagicMock()
    wrapped = wrap_with_digest_interval(inner, {"interval_seconds": 60})
    assert isinstance(wrapped, DigestIntervalNotifier)
    assert wrapped.interval_seconds == 60.0
    assert wrapped.inner is inner
