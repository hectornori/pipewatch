"""Tests for JitterNotifier."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from pipewatch.notifiers.jitter_notifier import JitterNotifier


class _FakeResult:
    def __init__(self, name: str = "pipe", success: bool = True):
        self.pipeline_name = name
        self.success = success


class _FakeNotifier:
    def __init__(self):
        self.received = []

    def send(self, result):
        self.received.append(result)


@pytest.fixture
def inner():
    return _FakeNotifier()


@pytest.fixture
def result():
    return _FakeResult()


def test_send_forwards_to_inner(inner, result):
    notifier = JitterNotifier(inner=inner, min_seconds=0, max_seconds=0, seed=42)
    notifier.send(result)
    assert inner.received == [result]


def test_send_calls_sleep(inner, result):
    notifier = JitterNotifier(inner=inner, min_seconds=0.1, max_seconds=0.5, seed=0)
    with patch("pipewatch.notifiers.jitter_notifier.time.sleep") as mock_sleep:
        notifier.send(result)
        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        assert 0.1 <= delay <= 0.5


def test_zero_range_no_sleep(inner, result):
    notifier = JitterNotifier(inner=inner, min_seconds=0, max_seconds=0, seed=7)
    with patch("pipewatch.notifiers.jitter_notifier.time.sleep") as mock_sleep:
        notifier.send(result)
        mock_sleep.assert_not_called()


def test_seed_produces_deterministic_delay(inner, result):
    n1 = JitterNotifier(inner=inner, min_seconds=1.0, max_seconds=10.0, seed=99)
    n2 = JitterNotifier(inner=_FakeNotifier(), min_seconds=1.0, max_seconds=10.0, seed=99)
    delays = []
    for notifier in (n1, n2):
        with patch("pipewatch.notifiers.jitter_notifier.time.sleep") as mock_sleep:
            notifier.send(result)
            delays.append(mock_sleep.call_args[0][0])
    assert delays[0] == delays[1]


def test_invalid_min_seconds_raises(inner):
    with pytest.raises(ValueError, match="min_seconds"):
        JitterNotifier(inner=inner, min_seconds=-1.0, max_seconds=5.0)


def test_invalid_max_less_than_min_raises(inner):
    with pytest.raises(ValueError, match="max_seconds"):
        JitterNotifier(inner=inner, min_seconds=5.0, max_seconds=1.0)


def test_inner_receives_original_result_unchanged(inner):
    r = _FakeResult(name="my_pipe", success=False)
    notifier = JitterNotifier(inner=inner, min_seconds=0, max_seconds=0)
    notifier.send(r)
    assert inner.received[0] is r
