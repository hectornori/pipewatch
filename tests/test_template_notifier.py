"""Tests for pipewatch.notifiers.template_notifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.template_notifier import (
    TemplateNotifier,
    template_notifier_from_config,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeResult:
    pipeline_name: str = "my_pipeline"
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[object] = []

    def send(self, result: object) -> None:
        self.received.append(result)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier) -> TemplateNotifier:
    return TemplateNotifier(inner=inner)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_send_forwards_to_inner(notifier: TemplateNotifier, inner: _FakeNotifier) -> None:
    result = _FakeResult()
    notifier.send(result)
    assert inner.received == [result]


def test_success_message_attached(notifier: TemplateNotifier) -> None:
    result = _FakeResult(pipeline_name="pipe_a", error_message=None)
    notifier.send(result)
    assert result.display_message == "[OK] pipe_a completed successfully."  # type: ignore[attr-defined]


def test_failure_message_attached(notifier: TemplateNotifier) -> None:
    result = _FakeResult(pipeline_name="pipe_b", error_message="timeout")
    notifier.send(result)
    assert result.display_message == "[FAIL] pipe_b failed: timeout"  # type: ignore[attr-defined]


def test_custom_success_template(inner: _FakeNotifier) -> None:
    n = TemplateNotifier(inner=inner, success_template="Pipeline ${pipeline} is ${status}.")
    result = _FakeResult(pipeline_name="etl")
    n.send(result)
    assert result.display_message == "Pipeline etl is ok."  # type: ignore[attr-defined]


def test_custom_failure_template(inner: _FakeNotifier) -> None:
    n = TemplateNotifier(
        inner=inner,
        failure_template="ALERT: ${pipeline} → ${error} [${status}]",
    )
    result = _FakeResult(pipeline_name="loader", error_message="disk full")
    n.send(result)
    assert result.display_message == "ALERT: loader → disk full [fail]"  # type: ignore[attr-defined]


def test_missing_template_variable_is_left_blank(inner: _FakeNotifier) -> None:
    """safe_substitute should not raise on unknown variables."""
    n = TemplateNotifier(inner=inner, failure_template="${pipeline}: ${unknown_var}")
    result = _FakeResult(pipeline_name="p", error_message="err")
    n.send(result)  # must not raise
    assert "p" in result.display_message  # type: ignore[attr-defined]


def test_template_notifier_from_config(inner: _FakeNotifier) -> None:
    cfg = {
        "success_template": "${pipeline} OK",
        "failure_template": "${pipeline} BROKEN: ${error}",
    }
    n = template_notifier_from_config(inner, cfg)
    result = _FakeResult(pipeline_name="x", error_message="boom")
    n.send(result)
    assert result.display_message == "x BROKEN: boom"  # type: ignore[attr-defined]


def test_template_notifier_from_config_defaults(inner: _FakeNotifier) -> None:
    n = template_notifier_from_config(inner, {})
    result = _FakeResult(pipeline_name="y")
    n.send(result)
    assert "[OK]" in result.display_message  # type: ignore[attr-defined]


def test_result_without_dict_does_not_raise(inner: _FakeNotifier) -> None:
    """If result has no __dict__ (e.g. a slot class), send must not crash."""

    class _Slotted:
        __slots__ = ("pipeline_name", "error_message")

        def __init__(self) -> None:
            self.pipeline_name = "z"
            self.error_message = None

    n = TemplateNotifier(inner=inner)
    n.send(_Slotted())  # should not raise
    assert len(inner.received) == 1
