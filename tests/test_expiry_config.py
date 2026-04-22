"""Tests for ExpiryConfig and helpers."""
from __future__ import annotations

import pytest

from pipewatch.expiry_config import ExpiryConfig, expiry_config_from_dict, wrap_with_expiry
from pipewatch.notifiers.expiry_notifier import ExpiryNotifier
from unittest.mock import MagicMock


def test_default_config_creates_successfully():
    cfg = ExpiryConfig(ttl_seconds=120)
    assert cfg.ttl_seconds == 120
    assert cfg.db_path == "pipewatch_expiry.db"


def test_zero_ttl_raises():
    with pytest.raises(ValueError, match="ttl_seconds"):
        ExpiryConfig(ttl_seconds=0)


def test_negative_ttl_raises():
    with pytest.raises(ValueError, match="ttl_seconds"):
        ExpiryConfig(ttl_seconds=-5)


def test_empty_db_path_raises():
    with pytest.raises(ValueError, match="db_path"):
        ExpiryConfig(ttl_seconds=60, db_path="")


def test_from_dict_minimal():
    cfg = expiry_config_from_dict({"ttl_seconds": 300})
    assert cfg.ttl_seconds == 300.0
    assert cfg.db_path == "pipewatch_expiry.db"


def test_from_dict_custom_db_path():
    cfg = expiry_config_from_dict({"ttl_seconds": 60, "db_path": "/tmp/expiry.db"})
    assert cfg.db_path == "/tmp/expiry.db"


def test_from_dict_missing_ttl_raises():
    with pytest.raises(KeyError, match="ttl_seconds"):
        expiry_config_from_dict({"db_path": "x.db"})


def test_wrap_with_expiry_returns_expiry_notifier(tmp_path):
    inner = MagicMock()
    cfg = ExpiryConfig(ttl_seconds=60, db_path=str(tmp_path / "e.db"))
    wrapped = wrap_with_expiry(inner, cfg)
    assert isinstance(wrapped, ExpiryNotifier)
    assert wrapped.ttl_seconds == 60
