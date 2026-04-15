"""Tests for FrequencyCapNotifier."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.frequency_cap_notifier import (
    FrequencyCapNotifier,
    FrequencyCapStore,
)


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe_a"
    success: bool = True
    error_message: str | None = None


@dataclass
class _FakeNotifier:
    calls: List[_FakeResult] = field(default_factory=list)

    def send(self, result) -> None:
        self.calls.append(result)


@pytest.fixture()
def store() -> FrequencyCapStore:
    return FrequencyCapStore(db_path=":memory:")


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner, store) -> FrequencyCapNotifier:
    return FrequencyCapNotifier(inner=inner, store=store, max_count=3, window_seconds=60.0)


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult()


def test_send_forwards_when_under_cap(notifier, inner, result):
    notifier.send(result)
    assert len(inner.calls) == 1


def test_send_blocked_when_cap_reached(notifier, inner, result):
    for _ in range(3):
        notifier.send(result)
    notifier.send(result)  # 4th call – should be blocked
    assert len(inner.calls) == 3


def test_send_counts_per_pipeline(store, inner):
    cap = FrequencyCapNotifier(inner=inner, store=store, max_count=2, window_seconds=60.0)
    r_a = _FakeResult(pipeline_name="pipe_a")
    r_b = _FakeResult(pipeline_name="pipe_b")
    cap.send(r_a)
    cap.send(r_a)
    cap.send(r_a)  # blocked for pipe_a
    cap.send(r_b)
    cap.send(r_b)
    cap.send(r_b)  # blocked for pipe_b
    assert len(inner.calls) == 4


def test_count_resets_after_window(store, inner):
    cap = FrequencyCapNotifier(inner=inner, store=store, max_count=1, window_seconds=0.05)
    r = _FakeResult()
    cap.send(r)  # accepted
    cap.send(r)  # blocked
    time.sleep(0.1)
    cap.send(r)  # window expired – accepted again
    assert len(inner.calls) == 2


def test_invalid_max_count_raises(store, inner):
    with pytest.raises(ValueError, match="max_count"):
        FrequencyCapNotifier(inner=inner, store=store, max_count=0)


def test_invalid_window_seconds_raises(store, inner):
    with pytest.raises(ValueError, match="window_seconds"):
        FrequencyCapNotifier(inner=inner, store=store, window_seconds=-1.0)


def test_store_count_in_window_zero_before_record(store):
    assert store.count_in_window("pipe_a", 60.0) == 0


def test_store_count_increments_on_record(store):
    store.record("pipe_a")
    store.record("pipe_a")
    assert store.count_in_window("pipe_a", 60.0) == 2
