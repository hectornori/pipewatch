"""Tests for SuppressionNotifier and SuppressionConfig."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from pipewatch.suppression import SuppressionStore
from pipewatch.notifiers.suppression_notifier import SuppressionNotifier
from pipewatch.suppression_config import (
    SuppressionConfig,
    suppression_config_from_dict,
    wrap_with_suppression,
)


class _FakeResult:
    def __init__(self, pipeline_name: str, success: bool, error_message: str | None = None):
        self.pipeline_name = pipeline_name
        self.success = success
        self.error_message = error_message


@pytest.fixture()
def store(tmp_path):
    return SuppressionStore(db_path=str(tmp_path / "sup.db"))


@pytest.fixture()
def inner():
    return MagicMock()


@pytest.fixture()
def notifier(store, inner):
    return SuppressionNotifier(inner=inner, store=store, cooldown_minutes=30)


@pytest.fixture()
def result():
    return _FakeResult("pipe_a", success=False, error_message="boom")


def test_send_forwards_success_immediately(notifier, inner):
    ok = _FakeResult("pipe_a", success=True)
    notifier.send(ok)
    inner.send.assert_called_once_with(ok)


def test_send_forwards_first_failure(notifier, inner, result):
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_send_suppresses_second_failure_within_cooldown(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    assert inner.send.call_count == 1


def test_send_not_suppressed_after_cooldown_expires(store, inner, result):
    notifier = SuppressionNotifier(inner=inner, store=store, cooldown_minutes=0)
    notifier.send(result)
    notifier.send(result)
    assert inner.send.call_count == 2


def test_suppression_isolated_per_pipeline(notifier, inner):
    a = _FakeResult("pipe_a", success=False)
    b = _FakeResult("pipe_b", success=False)
    notifier.send(a)
    notifier.send(b)
    assert inner.send.call_count == 2


def test_negative_cooldown_raises():
    with pytest.raises(ValueError, match="cooldown_minutes"):
        SuppressionNotifier(inner=MagicMock(), store=MagicMock(), cooldown_minutes=-1)


# --- SuppressionConfig ---

def test_default_config():
    cfg = SuppressionConfig()
    assert cfg.cooldown_minutes == 60
    assert cfg.db_path == "pipewatch_suppression.db"


def test_negative_cooldown_config_raises():
    with pytest.raises(ValueError):
        SuppressionConfig(cooldown_minutes=-5)


def test_empty_db_path_raises():
    with pytest.raises(ValueError):
        SuppressionConfig(db_path="")


def test_from_dict_defaults():
    cfg = suppression_config_from_dict({})
    assert cfg.cooldown_minutes == 60


def test_from_dict_custom():
    cfg = suppression_config_from_dict({"cooldown_minutes": 15, "db_path": "/tmp/s.db"})
    assert cfg.cooldown_minutes == 15
    assert cfg.db_path == "/tmp/s.db"


def test_wrap_with_suppression_returns_notifier(tmp_path):
    cfg = SuppressionConfig(db_path=str(tmp_path / "s.db"), cooldown_minutes=10)
    wrapped = wrap_with_suppression(MagicMock(), cfg)
    assert isinstance(wrapped, SuppressionNotifier)
    assert wrapped.cooldown_minutes == 10
