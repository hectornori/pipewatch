"""Tests for DigestIntervalNotifier."""
from __future__ import annotations

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.digest_interval_notifier import DigestIntervalNotifier, _IntervalDigestResult


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe-a"
    success: bool = True
    error_message: str = None


@pytest.fixture
def inner():
    return MagicMock()


@pytest.fixture
def notifier(inner):
    return DigestIntervalNotifier(inner=inner, interval_seconds=60.0)


@pytest.fixture
def result():
    return _FakeResult()


def test_send_buffers_without_flushing(notifier, inner, result):
    notifier.send(result)
    inner.send.assert_not_called()
    assert notifier.pending_count == 1


def test_pending_count_increments(notifier, result):
    notifier.send(result)
    notifier.send(result)
    assert notifier.pending_count == 2


def test_flush_forwards_digest(notifier, inner, result):
    notifier.send(result)
    notifier.flush()
    inner.send.assert_called_once()
    sent = inner.send.call_args[0][0]
    assert isinstance(sent, _IntervalDigestResult)
    assert len(sent.results) == 1


def test_flush_clears_buffer(notifier, result):
    notifier.send(result)
    notifier.flush()
    assert notifier.pending_count == 0


def test_flush_empty_buffer_does_nothing(notifier, inner):
    notifier.flush()
    inner.send.assert_not_called()


def test_auto_flush_when_interval_elapsed(inner, result):
    notifier = DigestIntervalNotifier(inner=inner, interval_seconds=0.0)
    notifier.send(result)
    inner.send.assert_called_once()


def test_no_auto_flush_before_interval(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    inner.send.assert_not_called()
    assert notifier.pending_count == 2


def test_digest_result_pipeline_name():
    r1 = _FakeResult(pipeline_name="a")
    r2 = _FakeResult(pipeline_name="b")
    d = _IntervalDigestResult([r1, r2])
    assert "a" in d.pipeline_name
    assert "b" in d.pipeline_name


def test_digest_result_success_all_pass():
    results = [_FakeResult(success=True), _FakeResult(success=True)]
    d = _IntervalDigestResult(results)
    assert d.success is True


def test_digest_result_success_false_when_any_fail():
    results = [_FakeResult(success=True), _FakeResult(success=False, error_message="boom")]
    d = _IntervalDigestResult(results)
    assert d.success is False


def test_digest_result_error_message_aggregated():
    results = [
        _FakeResult(success=False, error_message="err1"),
        _FakeResult(success=False, error_message="err2"),
    ]
    d = _IntervalDigestResult(results)
    assert "err1" in d.error_message
    assert "err2" in d.error_message


def test_multiple_flushes_each_batch_independent(inner):
    notifier = DigestIntervalNotifier(inner=inner, interval_seconds=60.0)
    notifier.send(_FakeResult(pipeline_name="x"))
    notifier.flush()
    notifier.send(_FakeResult(pipeline_name="y"))
    notifier.flush()
    assert inner.send.call_count == 2
    first_batch = inner.send.call_args_list[0][0][0]
    second_batch = inner.send.call_args_list[1][0][0]
    assert first_batch.results[0].pipeline_name == "x"
    assert second_batch.results[0].pipeline_name == "y"
