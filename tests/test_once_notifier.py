"""Tests for OnceNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.once_notifier import OnceLatchStore, OnceNotifier


@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.calls: List[_FakeResult] = []

    def send(self, result) -> None:
        self.calls.append(result)


@pytest.fixture()
def store() -> OnceLatchStore:
    return OnceLatchStore(db_path=":memory:")


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner, store) -> OnceNotifier:
    return OnceNotifier(inner=inner, store=store)


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult(pipeline_name="pipe_a", success=False, error_message="boom")


def test_first_failure_is_forwarded(notifier, inner, result):
    notifier.send(result)
    assert len(inner.calls) == 1


def test_second_failure_is_suppressed(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    assert len(inner.calls) == 1


def test_success_does_not_notify(notifier, inner):
    ok = _FakeResult(pipeline_name="pipe_a", success=True)
    notifier.send(ok)
    assert len(inner.calls) == 0


def test_latch_resets_after_success(notifier, inner, result):
    notifier.send(result)
    ok = _FakeResult(pipeline_name="pipe_a", success=True)
    notifier.send(ok)
    notifier.send(result)
    assert len(inner.calls) == 2


def test_different_pipelines_latched_independently(notifier, inner):
    fail_a = _FakeResult(pipeline_name="pipe_a", success=False)
    fail_b = _FakeResult(pipeline_name="pipe_b", success=False)
    notifier.send(fail_a)
    notifier.send(fail_b)
    notifier.send(fail_a)
    notifier.send(fail_b)
    assert len(inner.calls) == 2


def test_is_latched_false_before_any_failure(store):
    assert store.is_latched("pipe_x") is False


def test_latch_and_reset_cycle(store):
    store.latch("pipe_x")
    assert store.is_latched("pipe_x") is True
    store.reset("pipe_x")
    assert store.is_latched("pipe_x") is False
