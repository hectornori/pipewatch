"""Tests for GroupedNotifier."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.notifiers.grouped_notifier import GroupedNotifier


@pytest.fixture()
def ok_result() -> CheckResult:
    return CheckResult(pipeline_name="pipe_ok", success=True, error_message=None)


@pytest.fixture()
def fail_a() -> CheckResult:
    return CheckResult(pipeline_name="pipe_a", success=False, error_message="timeout")


@pytest.fixture()
def fail_b() -> CheckResult:
    return CheckResult(pipeline_name="pipe_b", success=False, error_message="connection refused")


@pytest.fixture()
def inner() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def notifier(inner: MagicMock) -> GroupedNotifier:
    return GroupedNotifier(inner=inner)


def test_send_buffers_result(notifier: GroupedNotifier, fail_a: CheckResult) -> None:
    notifier.send(fail_a)
    assert len(notifier.buffered) == 1
    assert notifier.buffered[0] is fail_a


def test_send_does_not_call_inner(notifier: GroupedNotifier, inner: MagicMock, fail_a: CheckResult) -> None:
    notifier.send(fail_a)
    inner.send.assert_not_called()


def test_flush_empty_buffer_does_nothing(notifier: GroupedNotifier, inner: MagicMock) -> None:
    notifier.flush()
    inner.send.assert_not_called()


def test_flush_only_successes_does_nothing(notifier: GroupedNotifier, inner: MagicMock, ok_result: CheckResult) -> None:
    notifier.send(ok_result)
    notifier.flush()
    inner.send.assert_not_called()
    assert notifier.buffered == []


def test_flush_sends_grouped_failure(notifier: GroupedNotifier, inner: MagicMock, fail_a: CheckResult, fail_b: CheckResult) -> None:
    notifier.send(fail_a)
    notifier.send(fail_b)
    notifier.flush()

    inner.send.assert_called_once()
    sent: CheckResult = inner.send.call_args[0][0]
    assert not sent.success
    assert "pipe_a" in sent.pipeline_name
    assert "pipe_b" in sent.pipeline_name


def test_flush_clears_buffer(notifier: GroupedNotifier, fail_a: CheckResult) -> None:
    notifier.send(fail_a)
    notifier.flush()
    assert notifier.buffered == []


def test_flush_error_message_contains_all_errors(notifier: GroupedNotifier, inner: MagicMock, fail_a: CheckResult, fail_b: CheckResult) -> None:
    notifier.send(fail_a)
    notifier.send(fail_b)
    notifier.flush()

    sent: CheckResult = inner.send.call_args[0][0]
    assert "timeout" in (sent.error_message or "")
    assert "connection refused" in (sent.error_message or "")


def test_flush_twice_second_is_noop(notifier: GroupedNotifier, inner: MagicMock, fail_a: CheckResult) -> None:
    notifier.send(fail_a)
    notifier.flush()
    notifier.flush()
    assert inner.send.call_count == 1


def test_buffered_returns_copy(notifier: GroupedNotifier, fail_a: CheckResult) -> None:
    notifier.send(fail_a)
    copy = notifier.buffered
    copy.clear()
    assert len(notifier.buffered) == 1
