"""Tests for DigestSummaryNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.notifiers.digest_summary_notifier import DigestSummaryNotifier


# ---------------------------------------------------------------------------
# Fake inner notifier
# ---------------------------------------------------------------------------

@dataclass
class _FakeNotifier:
    received: List = field(default_factory=list)

    def send(self, result) -> None:
        self.received.append(result)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier) -> DigestSummaryNotifier:
    return DigestSummaryNotifier(inner=inner, label="test-digest")


def _ok(name: str = "pipe") -> CheckResult:
    return CheckResult(pipeline_name=name, success=True, error_message=None)


def _fail(name: str = "pipe", msg: str = "boom") -> CheckResult:
    return CheckResult(pipeline_name=name, success=False, error_message=msg)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_send_does_not_forward_immediately(notifier, inner):
    notifier.send(_ok())
    assert len(inner.received) == 0


def test_pending_count_increments(notifier):
    assert notifier.pending_count == 0
    notifier.send(_ok())
    notifier.send(_fail())
    assert notifier.pending_count == 2


def test_flush_forwards_one_result(notifier, inner):
    notifier.send(_ok())
    notifier.send(_fail())
    notifier.flush()
    assert len(inner.received) == 1


def test_flush_clears_buffer(notifier):
    notifier.send(_ok())
    notifier.flush()
    assert notifier.pending_count == 0


def test_flush_on_empty_buffer_does_nothing(notifier, inner):
    notifier.flush()
    assert len(inner.received) == 0


def test_summary_success_when_all_pass(notifier, inner):
    notifier.send(_ok("a"))
    notifier.send(_ok("b"))
    notifier.flush()
    result = inner.received[0]
    assert result.success is True
    assert result.error_message is None


def test_summary_failure_when_any_fail(notifier, inner):
    notifier.send(_ok())
    notifier.send(_fail())
    notifier.flush()
    result = inner.received[0]
    assert result.success is False
    assert result.error_message is not None


def test_summary_text_contains_counts(notifier, inner):
    notifier.send(_ok())
    notifier.send(_fail())
    notifier.send(_fail())
    notifier.flush()
    text = inner.received[0].error_message
    assert "total=3" in text
    assert "passed=1" in text
    assert "failed=2" in text


def test_summary_pipeline_name_is_label(notifier, inner):
    notifier.send(_ok())
    notifier.flush()
    assert inner.received[0].pipeline_name == "test-digest"


def test_second_flush_after_new_sends(notifier, inner):
    notifier.send(_ok())
    notifier.flush()
    notifier.send(_fail())
    notifier.flush()
    assert len(inner.received) == 2
    assert inner.received[1].success is False
