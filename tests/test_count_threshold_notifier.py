"""Tests for CountThresholdNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.count_threshold_notifier import (
    CountThresholdNotifier,
    CountThresholdStore,
)


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe_a"
    success: bool = False


@dataclass
class _FakeNotifier:
    received: List = field(default_factory=list)

    def send(self, result) -> None:
        self.received.append(result)


@pytest.fixture
def store():
    return CountThresholdStore(db_path=":memory:")


@pytest.fixture
def inner():
    return _FakeNotifier()


@pytest.fixture
def notifier(inner, store):
    return CountThresholdNotifier(inner=inner, threshold=3, store=store)


@pytest.fixture
def result():
    return _FakeResult()


def test_does_not_forward_below_threshold(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    assert len(inner.received) == 0


def test_forwards_when_threshold_reached(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    notifier.send(result)
    assert len(inner.received) == 1


def test_resets_count_after_send(notifier, store, inner, result):
    for _ in range(3):
        notifier.send(result)
    assert store.count(result.pipeline_name) == 0


def test_no_reset_when_flag_off(inner, store, result):
    n = CountThresholdNotifier(inner=inner, threshold=2, store=store, reset_after_send=False)
    n.send(result)
    n.send(result)
    assert store.count(result.pipeline_name) == 2


def test_isolated_per_pipeline(inner, store):
    n = CountThresholdNotifier(inner=inner, threshold=2, store=store)
    r_a = _FakeResult(pipeline_name="a")
    r_b = _FakeResult(pipeline_name="b")
    n.send(r_a)
    n.send(r_b)
    assert len(inner.received) == 0
    n.send(r_a)
    assert len(inner.received) == 1
    assert inner.received[0].pipeline_name == "a"


def test_invalid_threshold_raises(inner, store):
    with pytest.raises(ValueError, match="threshold must be >= 1"):
        CountThresholdNotifier(inner=inner, threshold=0, store=store)


def test_threshold_of_one_always_forwards(inner, store, result):
    n = CountThresholdNotifier(inner=inner, threshold=1, store=store)
    n.send(result)
    assert len(inner.received) == 1
