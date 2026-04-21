"""Tests for QuarantineConfig and its helpers."""
from __future__ import annotations

import pytest

from pipewatch.quarantine_config import (
    QuarantineConfig,
    quarantine_config_from_dict,
    wrap_with_quarantine,
)
from pipewatch.notifiers.quarantine_notifier import QuarantineNotifier


class _FakeNotifier:
    def send(self, result) -> None:
        pass


def test_default_config_creates_successfully():
    cfg = QuarantineConfig()
    assert cfg.threshold == 3
    assert cfg.db_path == "pipewatch_quarantine.db"


def test_invalid_threshold_zero_raises():
    with pytest.raises(ValueError, match="threshold"):
        QuarantineConfig(threshold=0)


def test_invalid_threshold_negative_raises():
    with pytest.raises(ValueError, match="threshold"):
        QuarantineConfig(threshold=-1)


def test_empty_db_path_raises():
    with pytest.raises(ValueError, match="db_path"):
        QuarantineConfig(db_path="")


def test_from_dict_defaults():
    cfg = quarantine_config_from_dict({})
    assert cfg.threshold == 3
    assert cfg.db_path == "pipewatch_quarantine.db"


def test_from_dict_custom_values():
    cfg = quarantine_config_from_dict({"threshold": 5, "db_path": "/tmp/q.db"})
    assert cfg.threshold == 5
    assert cfg.db_path == "/tmp/q.db"


def test_from_dict_string_threshold_coerced():
    cfg = quarantine_config_from_dict({"threshold": "7"})
    assert cfg.threshold == 7


def test_wrap_with_quarantine_returns_notifier(tmp_path):
    cfg = QuarantineConfig(db_path=str(tmp_path / "q.db"))
    wrapped = wrap_with_quarantine(_FakeNotifier(), cfg)
    assert isinstance(wrapped, QuarantineNotifier)
    assert wrapped.threshold == cfg.threshold
