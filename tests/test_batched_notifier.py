"""Tests for BatchedNotifier."""
from __future__ import annotations

import time
from dataclasses import dataclass
from unittest.mock import MagicMock, call

import pytest

from pipewatch.notifiers.batched_notifier import BatchedNotifier


@dataclass
class _FakeResult:
    pipeline: str
    success: bool = True
    error_message: str | None = None


@pytest.fixture()
def inner():
    return MagicMock()


@pytest.fixture()
def notifier(inner):
    return BatchedNotifier(inner=inner, max_size=3, max_age_seconds=60.0)


def test_send_does_not_forward_immediately(notifier, inner):
    notifier.send(_FakeResult(pipeline="p1"))
    inner.send.assert_not_called()


def test_pending_count_increments(notifier):
    notifier.send(_FakeResult(pipeline="p1"))
    notifier.send(_FakeResult(pipeline="p2"))
    assert notifier.pending == 2


def test_flush_on_max_size(notifier, inner):
    r1 = _FakeResult(pipeline="p1")
    r2 = _FakeResult(pipeline="p2")
    r3 = _FakeResult(pipeline="p3")
    notifier.send(r1)
    notifier.send(r2)
    notifier.send(r3)  # triggers flush
    assert inner.send.call_count == 3
    inner.send.assert_has_calls([call(r1), call(r2), call(r3)])


def test_batch_cleared_after_flush(notifier, inner):
    for _ in range(3):
        notifier.send(_FakeResult(pipeline="p"))
    assert notifier.pending == 0


def test_explicit_flush_sends_partial_batch(notifier, inner):
    r = _FakeResult(pipeline="p1")
    notifier.send(r)
    notifier.flush()
    inner.send.assert_called_once_with(r)
    assert notifier.pending == 0


def test_flush_empty_batch_is_noop(notifier, inner):
    notifier.flush()
    inner.send.assert_not_called()


def test_flush_on_age_exceeded(inner, monkeypatch):
    """Simulate time passing so the age threshold triggers a flush."""
    notifier = BatchedNotifier(inner=inner, max_size=10, max_age_seconds=5.0)
    start = time.monotonic()
    monkeypatch.setattr("pipewatch.notifiers.batched_notifier.time.monotonic",
                        lambda: start + 6.0)
    notifier._batch_start = start
    notifier._batch.append(_FakeResult(pipeline="p1"))
    # Sending another item triggers the age check
    notifier.send(_FakeResult(pipeline="p2"))
    assert inner.send.call_count == 2


def test_invalid_max_size_raises():
    with pytest.raises(ValueError, match="max_size"):
        BatchedNotifier(inner=MagicMock(), max_size=0)


def test_invalid_max_age_raises():
    with pytest.raises(ValueError, match="max_age_seconds"):
        BatchedNotifier(inner=MagicMock(), max_age_seconds=-1.0)


def test_second_batch_starts_fresh(notifier, inner):
    for _ in range(3):
        notifier.send(_FakeResult(pipeline="first"))
    inner.reset_mock()
    notifier.send(_FakeResult(pipeline="second"))
    assert notifier.pending == 1
    inner.send.assert_not_called()
