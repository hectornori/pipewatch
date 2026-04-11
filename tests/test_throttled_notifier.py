"""Tests for ThrottledNotifier."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.throttle import ThrottleStore
from pipewatch.notifiers.throttled_notifier import ThrottledNotifier


@pytest.fixture
def _result():
    return CheckResult(pipeline_name="etl_daily", success=False, error_message="timeout")


@pytest.fixture
def store(tmp_path):
    return ThrottleStore(db_path=str(tmp_path / "throttle.db"))


@pytest.fixture
def inner():
    return MagicMock()


@pytest.fixture
def notifier(inner, store):
    return ThrottledNotifier(inner, store, channel="slack", min_interval_seconds=300)


def test_send_forwards_when_not_throttled(notifier, inner, _result):
    notifier.send(_result)
    inner.send.assert_called_once_with(_result)


def test_send_suppressed_on_second_call(notifier, inner, _result):
    notifier.send(_result)
    notifier.send(_result)
    assert inner.send.call_count == 1


def test_send_records_after_forwarding(notifier, store, _result):
    notifier.send(_result)
    assert store.last_sent_at("etl_daily", "slack") is not None


def test_different_pipeline_not_throttled(inner, store, _result):
    notifier = ThrottledNotifier(inner, store, channel="slack", min_interval_seconds=300)
    result_b = CheckResult(pipeline_name="etl_weekly", success=False, error_message="err")
    notifier.send(_result)
    notifier.send(result_b)
    assert inner.send.call_count == 2


def test_zero_interval_never_throttles(inner, store, _result):
    notifier = ThrottledNotifier(inner, store, channel="slack", min_interval_seconds=0)
    notifier.send(_result)
    notifier.send(_result)
    assert inner.send.call_count == 2


def test_negative_interval_raises(inner, store):
    with pytest.raises(ValueError, match="min_interval_seconds"):
        ThrottledNotifier(inner, store, channel="slack", min_interval_seconds=-1)


def test_channel_property(notifier):
    assert notifier.channel == "slack"


def test_min_interval_property(notifier):
    assert notifier.min_interval_seconds == 300
