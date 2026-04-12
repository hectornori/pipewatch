"""Tests for DigestNotifier."""
from __future__ import annotations

from typing import List

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.notifiers.digest_notifier import DigestNotifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[CheckResult] = []

    def send(self, result: CheckResult) -> None:
        self.received.append(result)


def _ok(name: str = "pipe") -> CheckResult:
    return CheckResult(pipeline_name=name, success=True, error_message=None)


def _fail(name: str = "pipe", msg: str = "boom") -> CheckResult:
    return CheckResult(pipeline_name=name, success=False, error_message=msg)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier) -> DigestNotifier:
    return DigestNotifier(inner, label="test-digest")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_pending_count_starts_at_zero(notifier: DigestNotifier) -> None:
    assert notifier.pending_count == 0


def test_send_increments_pending_count(notifier: DigestNotifier) -> None:
    notifier.send(_ok())
    notifier.send(_ok())
    assert notifier.pending_count == 2


def test_flush_with_empty_buffer_does_not_call_inner(
    notifier: DigestNotifier, inner: _FakeNotifier
) -> None:
    notifier.flush()
    assert inner.received == []


def test_flush_sends_exactly_one_message(
    notifier: DigestNotifier, inner: _FakeNotifier
) -> None:
    notifier.send(_ok())
    notifier.send(_fail())
    notifier.flush()
    assert len(inner.received) == 1


def test_flush_clears_buffer(notifier: DigestNotifier) -> None:
    notifier.send(_ok())
    notifier.flush()
    assert notifier.pending_count == 0


def test_flush_success_when_all_pass(
    notifier: DigestNotifier, inner: _FakeNotifier
) -> None:
    notifier.send(_ok("a"))
    notifier.send(_ok("b"))
    notifier.flush()
    assert inner.received[0].success is True
    assert inner.received[0].error_message is None


def test_flush_failure_when_any_fail(
    notifier: DigestNotifier, inner: _FakeNotifier
) -> None:
    notifier.send(_ok())
    notifier.send(_fail())
    notifier.flush()
    assert inner.received[0].success is False
    assert inner.received[0].error_message is not None


def test_flush_summary_contains_counts(
    notifier: DigestNotifier, inner: _FakeNotifier
) -> None:
    notifier.send(_ok())
    notifier.send(_fail())
    notifier.flush()
    msg = inner.received[0].error_message or ""
    assert "total=2" in msg
    assert "passed=1" in msg
    assert "failed=1" in msg


def test_flush_uses_label_as_pipeline_name(
    notifier: DigestNotifier, inner: _FakeNotifier
) -> None:
    notifier.send(_ok())
    notifier.flush()
    assert inner.received[0].pipeline_name == "test-digest"


def test_second_flush_after_new_sends(
    notifier: DigestNotifier, inner: _FakeNotifier
) -> None:
    notifier.send(_fail())
    notifier.flush()
    notifier.send(_ok())
    notifier.flush()
    assert len(inner.received) == 2
    # Second flush: all passed
    assert inner.received[1].success is True
