"""Tests for CapNotifier and CapStore."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.cap_notifier import CapNotifier, CapStore


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe_a"
    success: bool = True
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.calls: List[object] = []

    def send(self, result) -> None:
        self.calls.append(result)


@pytest.fixture()
def store(tmp_path):
    return CapStore(db_path=str(tmp_path / "cap.db"))


@pytest.fixture()
def inner():
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner, store):
    return CapNotifier(inner=inner, store=store, max_count=2, window_seconds=60)


@pytest.fixture()
def result():
    return _FakeResult()


def test_send_forwards_within_cap(notifier, inner, result):
    notifier.send(result)
    assert len(inner.calls) == 1


def test_send_forwards_up_to_cap(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    assert len(inner.calls) == 2


def test_send_suppressed_after_cap_reached(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    notifier.send(result)  # should be suppressed
    assert len(inner.calls) == 2


def test_cap_is_per_pipeline(store, inner):
    n = CapNotifier(inner=inner, store=store, max_count=1, window_seconds=60)
    n.send(_FakeResult(pipeline_name="pipe_a"))
    n.send(_FakeResult(pipeline_name="pipe_b"))
    assert len(inner.calls) == 2


def test_cap_resets_after_window(tmp_path):
    store = CapStore(db_path=str(tmp_path / "cap2.db"))
    inner = _FakeNotifier()
    n = CapNotifier(inner=inner, store=store, max_count=1, window_seconds=0.05)
    result = _FakeResult()
    n.send(result)          # allowed
    n.send(result)          # suppressed (cap reached)
    assert len(inner.calls) == 1
    time.sleep(0.1)
    n.send(result)          # window expired — allowed again
    assert len(inner.calls) == 2


def test_invalid_max_count_raises(store, inner):
    with pytest.raises(ValueError, match="max_count"):
        CapNotifier(inner=inner, store=store, max_count=0, window_seconds=60)


def test_invalid_window_raises(store, inner):
    with pytest.raises(ValueError, match="window_seconds"):
        CapNotifier(inner=inner, store=store, max_count=1, window_seconds=0)


def test_count_zero_before_any_record(store):
    assert store.count_since("pipe_a", time.time() - 60) == 0


def test_record_increments_count(store):
    store.record("pipe_a")
    store.record("pipe_a")
    assert store.count_since("pipe_a", time.time() - 60) == 2
