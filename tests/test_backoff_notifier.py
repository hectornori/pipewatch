"""Tests for BackoffNotifier."""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from pipewatch.notifiers.backoff_notifier import BackoffNotifier


class _FakeResult:
    pipeline = "test_pipeline"
    success = False
    error_message = "boom"


@pytest.fixture()
def inner():
    return MagicMock()


@pytest.fixture()
def notifier(inner):
    return BackoffNotifier(inner=inner, base_delay=0.01, max_delay=1.0, multiplier=2.0)


@pytest.fixture()
def result():
    return _FakeResult()


def test_send_forwards_on_first_success(notifier, inner, result):
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_no_sleep_on_first_send(notifier, inner, result):
    with patch("pipewatch.notifiers.backoff_notifier.time.sleep") as mock_sleep:
        notifier.send(result)
    mock_sleep.assert_not_called()


def test_consecutive_failures_increment(notifier, inner, result):
    inner.send.side_effect = RuntimeError("fail")
    for _ in range(3):
        with pytest.raises(RuntimeError):
            notifier.send(result)
    assert notifier._consecutive_failures == 3


def test_success_resets_consecutive_failures(notifier, inner, result):
    inner.send.side_effect = [RuntimeError("fail"), None]
    with pytest.raises(RuntimeError):
        notifier.send(result)
    notifier.send(result)
    assert notifier._consecutive_failures == 0


def test_delay_grows_exponentially(notifier, inner, result):
    inner.send.side_effect = RuntimeError("fail")
    delays = []
    with patch("pipewatch.notifiers.backoff_notifier.time.sleep", side_effect=lambda d: delays.append(d)):
        for _ in range(4):
            with pytest.raises(RuntimeError):
                notifier.send(result)
    # first send: no sleep; subsequent sends: 0.01, 0.02, 0.04
    assert delays == [0.01, 0.02, 0.04]


def test_delay_capped_at_max_delay(notifier, inner, result):
    inner.send.side_effect = RuntimeError("fail")
    # force many failures so delay would exceed max_delay
    notifier._consecutive_failures = 100
    with patch("pipewatch.notifiers.backoff_notifier.time.sleep") as mock_sleep:
        with pytest.raises(RuntimeError):
            notifier.send(result)
    mock_sleep.assert_called_once()
    assert mock_sleep.call_args[0][0] == notifier.max_delay


def test_invalid_base_delay_raises():
    with pytest.raises(ValueError, match="base_delay"):
        BackoffNotifier(inner=MagicMock(), base_delay=0.0)


def test_invalid_max_delay_raises():
    with pytest.raises(ValueError, match="max_delay"):
        BackoffNotifier(inner=MagicMock(), base_delay=5.0, max_delay=1.0)


def test_invalid_multiplier_raises():
    with pytest.raises(ValueError, match="multiplier"):
        BackoffNotifier(inner=MagicMock(), base_delay=1.0, multiplier=0.5)
