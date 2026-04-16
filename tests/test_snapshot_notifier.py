"""Tests for SnapshotNotifier."""
from __future__ import annotations

import pytest

from pipewatch.snapshot import SnapshotStore
from pipewatch.notifiers.snapshot_notifier import SnapshotNotifier


class _FakeResult:
    def __init__(self, name: str, success: bool, error: str | None = None):
        self.pipeline_name = name
        self.success = success
        self.error_message = error


class _FakeNotifier:
    def __init__(self):
        self.calls: list = []

    def send(self, result) -> None:
        self.calls.append(result)


@pytest.fixture
def store():
    return SnapshotStore(db_path=":memory:")


@pytest.fixture
def inner():
    return _FakeNotifier()


@pytest.fixture
def notifier(inner, store):
    return SnapshotNotifier(inner=inner, store=store)


@pytest.fixture
def result():
    return _FakeResult("pipe_a", success=True)


def test_send_forwards_on_first_result(notifier, inner, result):
    notifier.send(result)
    assert len(inner.calls) == 1


def test_send_suppresses_when_state_unchanged(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    assert len(inner.calls) == 1


def test_send_forwards_when_success_changes(notifier, inner):
    notifier.send(_FakeResult("pipe_a", success=True))
    notifier.send(_FakeResult("pipe_a", success=False, error="boom"))
    assert len(inner.calls) == 2


def test_send_forwards_when_error_message_changes(notifier, inner):
    notifier.send(_FakeResult("pipe_a", success=False, error="err1"))
    notifier.send(_FakeResult("pipe_a", success=False, error="err2"))
    assert len(inner.calls) == 2


def test_send_suppresses_identical_failure(notifier, inner):
    notifier.send(_FakeResult("pipe_a", success=False, error="boom"))
    notifier.send(_FakeResult("pipe_a", success=False, error="boom"))
    assert len(inner.calls) == 1


def test_different_pipelines_tracked_independently(notifier, inner):
    notifier.send(_FakeResult("pipe_a", success=True))
    notifier.send(_FakeResult("pipe_b", success=True))
    assert len(inner.calls) == 2


def test_sent_count_increments_on_forward(notifier, result):
    notifier.send(result)
    notifier.send(result)
    assert notifier.sent_count == 1


def test_recovery_detected(notifier, inner):
    notifier.send(_FakeResult("pipe_a", success=False, error="down"))
    notifier.send(_FakeResult("pipe_a", success=True))
    assert len(inner.calls) == 2
