"""Tests for DeadLetterNotifier and DeadLetterStore."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass
from pipewatch.notifiers.dead_letter_notifier import (
    DeadLetterNotifier,
    DeadLetterStore,
)


@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool
    error_message: str | None = None


@pytest.fixture
def store() -> DeadLetterStore:
    return DeadLetterStore(db_path=":memory:")


@pytest.fixture
def inner() -> MagicMock:
    return MagicMock()


@pytest.fixture
def notifier(inner, store) -> DeadLetterNotifier:
    return DeadLetterNotifier(inner=inner, store=store)


@pytest.fixture
def result() -> _FakeResult:
    return _FakeResult(pipeline_name="pipe_a", success=False, error_message="timeout")


def test_send_forwards_to_inner(notifier, inner, result):
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_no_dead_letter_on_success(notifier, store, result):
    notifier.send(result)
    assert store.get_all() == []


def test_dead_letter_recorded_on_failure(inner, store, result):
    inner.send.side_effect = RuntimeError("connection refused")
    notifier = DeadLetterNotifier(inner=inner, store=store)
    notifier.send(result)  # should not raise
    entries = store.get_all()
    assert len(entries) == 1
    assert entries[0].pipeline == "pipe_a"
    assert "connection refused" in entries[0].error


def test_dead_letter_payload_contains_result_repr(inner, store, result):
    inner.send.side_effect = RuntimeError("boom")
    notifier = DeadLetterNotifier(inner=inner, store=store)
    notifier.send(result)
    entries = store.get_all()
    assert "pipe_a" in entries[0].payload


def test_multiple_failures_accumulate(inner, store):
    inner.send.side_effect = RuntimeError("err")
    notifier = DeadLetterNotifier(inner=inner, store=store)
    for name in ["p1", "p2", "p3"]:
        notifier.send(_FakeResult(pipeline_name=name, success=False))
    assert len(store.get_all()) == 3


def test_clear_removes_all_entries(inner, store, result):
    inner.send.side_effect = RuntimeError("err")
    notifier = DeadLetterNotifier(inner=inner, store=store)
    notifier.send(result)
    store.clear()
    assert store.get_all() == []


def test_pipeline_name_falls_back_to_unknown(inner, store):
    inner.send.side_effect = RuntimeError("err")
    notifier = DeadLetterNotifier(inner=inner, store=store)
    notifier.send(object())  # no pipeline_name attr
    entries = store.get_all()
    assert entries[0].pipeline == "unknown"
