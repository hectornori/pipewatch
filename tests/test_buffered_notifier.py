"""Tests for BufferedNotifier."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.buffered_notifier import BufferedNotifier


@dataclass
class _FakeResult:
    pipeline: str
    success: bool = True
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[object] = []

    def send(self, result: object) -> None:
        self.received.append(result)


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier) -> BufferedNotifier:
    return BufferedNotifier(inner=inner, max_size=3, max_age_seconds=60.0)


def test_send_does_not_forward_immediately(notifier: BufferedNotifier, inner: _FakeNotifier) -> None:
    notifier.send(_FakeResult("pipe-a"))
    assert inner.received == []


def test_pending_count_increments(notifier: BufferedNotifier) -> None:
    notifier.send(_FakeResult("pipe-a"))
    notifier.send(_FakeResult("pipe-b"))
    assert notifier.pending_count == 2


def test_flush_on_max_size(notifier: BufferedNotifier, inner: _FakeNotifier) -> None:
    for i in range(3):
        notifier.send(_FakeResult(f"pipe-{i}"))
    assert len(inner.received) == 3
    assert notifier.pending_count == 0


def test_manual_flush(notifier: BufferedNotifier, inner: _FakeNotifier) -> None:
    notifier.send(_FakeResult("pipe-a"))
    notifier.send(_FakeResult("pipe-b"))
    notifier.flush()
    assert len(inner.received) == 2
    assert notifier.pending_count == 0


def test_flush_empty_buffer_is_noop(notifier: BufferedNotifier, inner: _FakeNotifier) -> None:
    notifier.flush()
    assert inner.received == []


def test_flush_resets_window_start(notifier: BufferedNotifier) -> None:
    notifier.send(_FakeResult("pipe-a"))
    notifier.flush()
    assert notifier._window_start == 0.0


def test_flush_on_age_threshold(inner: _FakeNotifier) -> None:
    notifier = BufferedNotifier(inner=inner, max_size=100, max_age_seconds=0.05)
    notifier.send(_FakeResult("pipe-a"))
    time.sleep(0.1)
    notifier.send(_FakeResult("pipe-b"))  # triggers age check
    assert len(inner.received) == 2


def test_inner_exception_does_not_lose_other_items(inner: _FakeNotifier) -> None:
    call_count = 0

    class _Boom:
        def send(self, result: object) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("boom")

    boom = _Boom()
    notifier = BufferedNotifier(inner=boom, max_size=2, max_age_seconds=60.0)
    notifier.send(_FakeResult("pipe-a"))
    notifier.send(_FakeResult("pipe-b"))  # triggers flush
    assert call_count == 2  # both attempts were made


def test_invalid_max_size_raises() -> None:
    with pytest.raises(ValueError, match="max_size"):
        BufferedNotifier(inner=_FakeNotifier(), max_size=0)


def test_invalid_max_age_raises() -> None:
    with pytest.raises(ValueError, match="max_age_seconds"):
        BufferedNotifier(inner=_FakeNotifier(), max_size=5, max_age_seconds=0)
