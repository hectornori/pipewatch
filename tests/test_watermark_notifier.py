"""Tests for WatermarkNotifier."""
from __future__ import annotations

import pytest
from dataclasses import dataclass
from unittest.mock import MagicMock

from pipewatch.notifiers.watermark_notifier import WatermarkNotifier


@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool
    error_message: str | None = None


@pytest.fixture()
def inner():
    return MagicMock()


@pytest.fixture()
def notifier(inner):
    return WatermarkNotifier(inner=inner, threshold=3)


@pytest.fixture()
def result():
    return _FakeResult(pipeline_name="pipe_a", success=False)


def test_invalid_threshold_zero_raises(inner):
    with pytest.raises(ValueError, match="threshold"):
        WatermarkNotifier(inner=inner, threshold=0)


def test_invalid_threshold_negative_raises(inner):
    with pytest.raises(ValueError, match="threshold"):
        WatermarkNotifier(inner=inner, threshold=-1)


def test_below_threshold_does_not_forward(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    inner.send.assert_not_called()


def test_at_threshold_forwards(notifier, inner, result):
    for _ in range(3):
        notifier.send(result)
    assert inner.send.call_count == 1


def test_above_threshold_keeps_forwarding(notifier, inner, result):
    for _ in range(5):
        notifier.send(result)
    assert inner.send.call_count == 3


def test_success_resets_count(notifier, inner):
    fail = _FakeResult(pipeline_name="pipe_a", success=False)
    ok = _FakeResult(pipeline_name="pipe_a", success=True)

    notifier.send(fail)
    notifier.send(fail)
    notifier.send(ok)  # reset
    notifier.send(fail)
    notifier.send(fail)

    # Never reached threshold before reset, and only 2 after reset
    inner.send.assert_not_called()


def test_success_not_forwarded(notifier, inner):
    ok = _FakeResult(pipeline_name="pipe_a", success=True)
    notifier.send(ok)
    inner.send.assert_not_called()


def test_counts_isolated_per_pipeline(notifier, inner):
    a = _FakeResult(pipeline_name="pipe_a", success=False)
    b = _FakeResult(pipeline_name="pipe_b", success=False)

    for _ in range(2):
        notifier.send(a)
    for _ in range(3):
        notifier.send(b)

    # pipe_a never reached threshold; pipe_b did once
    assert inner.send.call_count == 1
    assert notifier.counts["pipe_a"] == 2
    assert notifier.counts["pipe_b"] == 3


def test_manual_reset_clears_count(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    notifier.reset("pipe_a")
    assert notifier.counts == {}


def test_threshold_one_forwards_immediately(inner):
    n = WatermarkNotifier(inner=inner, threshold=1)
    r = _FakeResult(pipeline_name="x", success=False)
    n.send(r)
    inner.send.assert_called_once_with(r)
