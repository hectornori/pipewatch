"""Tests for QuarantineNotifier and QuarantineStore."""
from __future__ import annotations

import pytest

from pipewatch.notifiers.quarantine_notifier import (
    QuarantineNotifier,
    QuarantineStore,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, pipeline: str, success: bool, error: str | None = None):
        self.pipeline = pipeline
        self.success = success
        self.error_message = error


class _FakeNotifier:
    def __init__(self):
        self.received: list = []

    def send(self, result) -> None:
        self.received.append(result)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    return QuarantineStore(db_path=str(tmp_path / "q.db"))


@pytest.fixture
def inner():
    return _FakeNotifier()


@pytest.fixture
def notifier(inner, store):
    return QuarantineNotifier(inner=inner, store=store, threshold=3)


@pytest.fixture
def result():
    return _FakeResult(pipeline="pipe_a", success=False, error="boom")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_send_forwards_success_immediately(notifier, inner):
    r = _FakeResult("pipe_a", success=True)
    notifier.send(r)
    assert inner.received == [r]


def test_send_forwards_first_failure(notifier, inner, result):
    notifier.send(result)
    assert inner.received == [result]


def test_send_forwards_failures_below_threshold(notifier, inner):
    for _ in range(2):  # threshold=3, so 2 failures should still forward
        r = _FakeResult("pipe_a", success=False)
        notifier.send(r)
    assert len(inner.received) == 2


def test_send_quarantines_at_threshold(notifier, inner, store):
    for _ in range(3):
        notifier.send(_FakeResult("pipe_a", success=False))
    assert store.is_quarantined("pipe_a")


def test_send_suppresses_after_quarantine(notifier, inner, store):
    for _ in range(3):
        notifier.send(_FakeResult("pipe_a", success=False))
    # 4th failure should be suppressed
    notifier.send(_FakeResult("pipe_a", success=False))
    assert len(inner.received) == 3


def test_success_clears_quarantine(notifier, inner, store):
    for _ in range(3):
        notifier.send(_FakeResult("pipe_a", success=False))
    assert store.is_quarantined("pipe_a")
    notifier.send(_FakeResult("pipe_a", success=True))
    assert not store.is_quarantined("pipe_a")


def test_success_after_quarantine_resumes_alerts(notifier, inner):
    for _ in range(3):
        notifier.send(_FakeResult("pipe_a", success=False))
    notifier.send(_FakeResult("pipe_a", success=True))
    # after recovery a new failure should be forwarded again
    notifier.send(_FakeResult("pipe_a", success=False))
    # 3 quarantine + 1 success + 1 post-recovery failure = 5
    assert len(inner.received) == 5


def test_pipelines_are_isolated(notifier, inner, store):
    for _ in range(3):
        notifier.send(_FakeResult("pipe_a", success=False))
    # pipe_b should not be affected
    notifier.send(_FakeResult("pipe_b", success=False))
    assert not store.is_quarantined("pipe_b")


def test_invalid_threshold_raises(inner, store):
    with pytest.raises(ValueError, match="threshold"):
        QuarantineNotifier(inner=inner, store=store, threshold=0)
