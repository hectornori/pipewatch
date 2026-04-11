"""Tests for CooldownStore and CooldownNotifier."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.cooldown import CooldownStore
from pipewatch.monitor import CheckResult
from pipewatch.notifiers.cooldown_notifier import CooldownNotifier


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path):
    return CooldownStore(db_path=str(tmp_path / "cooldown.db"), default_minutes=30)


@pytest.fixture()
def _ok_result():
    return CheckResult(pipeline_name="pipe_a", success=True, error_message=None)


@pytest.fixture()
def _fail_result():
    return CheckResult(pipeline_name="pipe_a", success=False, error_message="boom")


# ---------------------------------------------------------------------------
# CooldownStore tests
# ---------------------------------------------------------------------------


def test_last_alerted_at_none_before_record(store):
    assert store.last_alerted_at("pipe_a") is None


def test_not_cooling_down_before_record(store):
    assert store.is_cooling_down("pipe_a") is False


def test_record_stores_timestamp(store):
    store.record("pipe_a")
    ts = store.last_alerted_at("pipe_a")
    assert ts is not None
    assert isinstance(ts, datetime)


def test_cooling_down_immediately_after_record(store):
    store.record("pipe_a")
    assert store.is_cooling_down("pipe_a") is True


def test_not_cooling_down_after_window_expires(store):
    past = datetime.now(timezone.utc) - timedelta(minutes=31)
    with patch("pipewatch.cooldown.datetime") as mock_dt:
        mock_dt.now.return_value = past
        mock_dt.fromisoformat = datetime.fromisoformat
        store.record("pipe_a")
    # Now check without mocking — 31 min have elapsed, window is 30 min.
    assert store.is_cooling_down("pipe_a") is False


def test_clear_removes_cooldown(store):
    store.record("pipe_a")
    store.clear("pipe_a")
    assert store.last_alerted_at("pipe_a") is None
    assert store.is_cooling_down("pipe_a") is False


def test_invalid_default_minutes_raises():
    with pytest.raises(ValueError):
        CooldownStore(db_path=":memory:", default_minutes=-1)


def test_per_call_cooldown_overrides_default(store):
    store.record("pipe_a")
    # 0-minute cooldown means never cooling down.
    assert store.is_cooling_down("pipe_a", cooldown_minutes=0) is False


# ---------------------------------------------------------------------------
# CooldownNotifier tests
# ---------------------------------------------------------------------------


def test_send_forwards_when_not_cooling_down(store, _fail_result):
    inner = MagicMock()
    notifier = CooldownNotifier(inner, store, cooldown_minutes=30)
    notifier.send(_fail_result)
    inner.send.assert_called_once_with(_fail_result)


def test_send_suppressed_during_cooldown(store, _fail_result):
    inner = MagicMock()
    notifier = CooldownNotifier(inner, store, cooldown_minutes=30)
    store.record(_fail_result.pipeline_name)
    notifier.send(_fail_result)
    inner.send.assert_not_called()


def test_send_records_cooldown_after_alert(store, _fail_result):
    inner = MagicMock()
    notifier = CooldownNotifier(inner, store, cooldown_minutes=30)
    notifier.send(_fail_result)
    assert store.is_cooling_down(_fail_result.pipeline_name) is True


def test_recovery_clears_cooldown_and_forwards(store, _ok_result):
    inner = MagicMock()
    notifier = CooldownNotifier(inner, store, cooldown_minutes=30)
    store.record(_ok_result.pipeline_name)
    notifier.send(_ok_result)
    inner.send.assert_called_once_with(_ok_result)
    assert store.last_alerted_at(_ok_result.pipeline_name) is None
