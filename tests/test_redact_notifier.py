"""Tests for RedactNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from pipewatch.notifiers.redact_notifier import RedactNotifier, _DEFAULT_PATTERNS


@dataclass
class _FakeResult:
    pipeline: str
    success: bool
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: list[Any] = []

    def send(self, result: Any) -> None:
        self.received.append(result)


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier) -> RedactNotifier:
    return RedactNotifier(inner=inner)


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult(pipeline="pipe", success=False, error_message="normal error")


def test_send_forwards_clean_message(notifier: RedactNotifier, inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier.send(result)
    assert inner.received[0].error_message == "normal error"


def test_send_redacts_password_keyword(inner: _FakeNotifier) -> None:
    n = RedactNotifier(inner=inner)
    r = _FakeResult(pipeline="p", success=False, error_message="password is wrong")
    n.send(r)
    assert "password" not in inner.received[0].error_message
    assert "[REDACTED]" in inner.received[0].error_message


def test_send_redacts_token_keyword(inner: _FakeNotifier) -> None:
    n = RedactNotifier(inner=inner)
    r = _FakeResult(pipeline="p", success=False, error_message="invalid token abc123")
    n.send(r)
    assert "token" not in inner.received[0].error_message


def test_send_redacts_api_key_keyword(inner: _FakeNotifier) -> None:
    n = RedactNotifier(inner=inner)
    r = _FakeResult(pipeline="p", success=False, error_message="api_key=supersecret")
    n.send(r)
    assert "api_key" not in inner.received[0].error_message


def test_none_error_message_passed_through(notifier: RedactNotifier, inner: _FakeNotifier) -> None:
    r = _FakeResult(pipeline="p", success=True, error_message=None)
    notifier.send(r)
    assert inner.received[0].error_message is None


def test_other_attributes_unchanged(notifier: RedactNotifier, inner: _FakeNotifier) -> None:
    r = _FakeResult(pipeline="my-pipeline", success=False, error_message="secret leak")
    notifier.send(r)
    assert inner.received[0].pipeline == "my-pipeline"
    assert inner.received[0].success is False


def test_custom_patterns_applied(inner: _FakeNotifier) -> None:
    n = RedactNotifier(inner=inner, patterns=[r"banana"])
    r = _FakeResult(pipeline="p", success=False, error_message="banana split")
    n.send(r)
    assert "banana" not in inner.received[0].error_message


def test_custom_replacement_used(inner: _FakeNotifier) -> None:
    n = RedactNotifier(inner=inner, patterns=[r"secret"], replacement="***")
    r = _FakeResult(pipeline="p", success=False, error_message="my secret value")
    n.send(r)
    assert "***" in inner.received[0].error_message
    assert "secret" not in inner.received[0].error_message


def test_default_patterns_list_is_not_empty() -> None:
    assert len(_DEFAULT_PATTERNS) > 0
