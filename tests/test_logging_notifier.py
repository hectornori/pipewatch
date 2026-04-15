"""Tests for LoggingNotifier."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

import pytest

from pipewatch.notifiers.logging_notifier import LoggingNotifier


@dataclass
class _FakeResult:
    pipeline_name: str = "my_pipeline"
    success: bool = True
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[object] = []

    def send(self, result: object) -> None:
        self.received.append(result)


class _BrokenNotifier:
    def send(self, result: object) -> None:
        raise RuntimeError("downstream failure")


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier) -> LoggingNotifier:
    return LoggingNotifier(inner=inner)


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult()


def test_send_forwards_to_inner(notifier: LoggingNotifier, inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier.send(result)
    assert inner.received == [result]


def test_send_logs_pipeline_name(notifier: LoggingNotifier, result: _FakeResult, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="pipewatch.notifiers.logging_notifier"):
        notifier.send(result)
    assert "my_pipeline" in caplog.text


def test_send_logs_ok_status(notifier: LoggingNotifier, result: _FakeResult, caplog: pytest.LogCaptureFixture) -> None:
    result.success = True
    with caplog.at_level(logging.INFO, logger="pipewatch.notifiers.logging_notifier"):
        notifier.send(result)
    assert "ok" in caplog.text


def test_send_logs_fail_status(notifier: LoggingNotifier, result: _FakeResult, caplog: pytest.LogCaptureFixture) -> None:
    result.success = False
    result.error_message = "timeout"
    with caplog.at_level(logging.INFO, logger="pipewatch.notifiers.logging_notifier"):
            assert "fail" in caplog.text


def test_send_logs_error_message_when_present(notifier: LoggingNotifier, result: _FakeResult, caplog: pytest.LogCaptureFixture) -> None:
    result.success = False
    result.error_message = "connection refused"
    with caplog.at_level(logging.INFO, logger="pipewatch.notifiers.logging_notifier"):
        notifier.send(result)
    assert "connection refused" in caplog.text


def test_send_omits_error_when_include_error_false(result: _FakeResult, inner: _FakeNotifier, caplog: pytest.LogCaptureFixture) -> None:
    n = LoggingNotifier(inner=inner, include_error=False)
    result.success = False
    result.error_message = "secret error"
    with caplog.at_level(logging.INFO, logger="pipewatch.notifiers.logging_notifier"):
        n.send(result)
    assert "secret error" not in caplog.text


def test_send_reraises_inner_exception(result: _FakeResult) -> None:
    n = LoggingNotifier(inner=_BrokenNotifier())
    with pytest.raises(RuntimeError, match="downstream failure"):
        n.send(result)


def test_send_still_logs_before_inner_exception(
    result: _FakeResult, caplog: pytest.LogCaptureFixture
) -> None:
    """Logging should occur even when the inner notifier raises."""
    n = LoggingNotifier(inner=_BrokenNotifier())
    with caplog.at_level(logging.INFO, logger="pipewatch.notifiers.logging_notifier"):
        with pytest.raises(RuntimeError):
            n.send(result)
    assert "my_pipeline" in caplog.text
