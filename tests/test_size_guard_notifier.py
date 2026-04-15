"""Tests for SizeGuardNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

import pytest

from pipewatch.notifiers.size_guard_notifier import SizeGuardNotifier


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

@dataclass
class _FakeResult:
    pipeline_name: str = "pipe_a"
    success: bool = True
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[Any] = []

    def send(self, result: Any) -> None:
        self.received.append(result)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult()


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_invalid_max_bytes_raises(inner: _FakeNotifier) -> None:
    with pytest.raises(ValueError, match="max_bytes"):
        SizeGuardNotifier(inner=inner, max_bytes=0)


def test_negative_max_bytes_raises(inner: _FakeNotifier) -> None:
    with pytest.raises(ValueError):
        SizeGuardNotifier(inner=inner, max_bytes=-10)


# ---------------------------------------------------------------------------
# Pass-through when within limit
# ---------------------------------------------------------------------------

def test_small_payload_forwarded(inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier = SizeGuardNotifier(inner=inner, max_bytes=4096)
    notifier.send(result)
    assert len(inner.received) == 1
    assert inner.received[0] is result


# ---------------------------------------------------------------------------
# Drop mode (truncate=False)
# ---------------------------------------------------------------------------

def test_oversized_payload_dropped_by_default(inner: _FakeNotifier) -> None:
    big_error = "x" * 10_000
    result = _FakeResult(pipeline_name="pipe_b", success=False, error_message=big_error)
    notifier = SizeGuardNotifier(inner=inner, max_bytes=64, truncate=False)
    notifier.send(result)
    assert inner.received == []


# ---------------------------------------------------------------------------
# Truncate mode
# ---------------------------------------------------------------------------

def test_oversized_payload_truncated_when_flag_set(inner: _FakeNotifier) -> None:
    big_error = "e" * 5_000
    result = _FakeResult(pipeline_name="pipe_c", success=False, error_message=big_error)
    notifier = SizeGuardNotifier(inner=inner, max_bytes=128, truncate=True)
    notifier.send(result)
    assert len(inner.received) == 1


def test_truncated_result_ends_with_ellipsis(inner: _FakeNotifier) -> None:
    big_error = "a" * 5_000
    result = _FakeResult(pipeline_name="pipe_d", success=False, error_message=big_error)
    notifier = SizeGuardNotifier(inner=inner, max_bytes=128, truncate=True)
    notifier.send(result)
    sent = inner.received[0]
    assert sent.error_message.endswith("...")


def test_truncated_result_preserves_pipeline_name(inner: _FakeNotifier) -> None:
    big_error = "b" * 5_000
    result = _FakeResult(pipeline_name="my_pipeline", success=False, error_message=big_error)
    notifier = SizeGuardNotifier(inner=inner, max_bytes=128, truncate=True)
    notifier.send(result)
    sent = inner.received[0]
    assert sent.pipeline_name == "my_pipeline"


def test_truncated_result_preserves_success_flag(inner: _FakeNotifier) -> None:
    big_error = "c" * 5_000
    result = _FakeResult(pipeline_name="pipe_e", success=False, error_message=big_error)
    notifier = SizeGuardNotifier(inner=inner, max_bytes=128, truncate=True)
    notifier.send(result)
    assert inner.received[0].success is False
