"""Tests for TimeoutNotifier."""
from __future__ import annotations

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.timeout_notifier import TimeoutNotifier


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe-a"
    success: bool = True
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult()


@pytest.fixture()
def inner() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def notifier(inner: MagicMock) -> TimeoutNotifier:
    return TimeoutNotifier(inner=inner, timeout_seconds=2.0)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_invalid_timeout_raises() -> None:
    with pytest.raises(ValueError, match="positive"):
        TimeoutNotifier(inner=MagicMock(), timeout_seconds=0)


def test_negative_timeout_raises() -> None:
    with pytest.raises(ValueError, match="positive"):
        TimeoutNotifier(inner=MagicMock(), timeout_seconds=-1.0)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_send_forwards_to_inner(notifier: TimeoutNotifier, inner: MagicMock, result: _FakeResult) -> None:
    notifier.send(result)
    inner.send.assert_called_once_with(result)


# ---------------------------------------------------------------------------
# Timeout behaviour
# ---------------------------------------------------------------------------


def test_send_returns_when_inner_hangs(result: _FakeResult) -> None:
    """If the inner notifier blocks, send() should return after the timeout."""

    class _SlowNotifier:
        def send(self, r) -> None:  # noqa: ANN001
            time.sleep(10)

    notifier = TimeoutNotifier(inner=_SlowNotifier(), timeout_seconds=0.1)
    start = time.monotonic()
    notifier.send(result)  # must not block indefinitely
    elapsed = time.monotonic() - start
    assert elapsed < 2.0, f"send blocked for {elapsed:.2f}s"


def test_send_logs_warning_on_timeout(result: _FakeResult, caplog: pytest.LogCaptureFixture) -> None:
    class _SlowNotifier:
        def send(self, r) -> None:  # noqa: ANN001
            time.sleep(10)

    notifier = TimeoutNotifier(inner=_SlowNotifier(), timeout_seconds=0.1)
    import logging
    with caplog.at_level(logging.WARNING, logger="pipewatch.notifiers.timeout_notifier"):
        notifier.send(result)
    assert "timed out" in caplog.text


# ---------------------------------------------------------------------------
# Exception propagation
# ---------------------------------------------------------------------------


def test_send_raises_when_inner_raises(result: _FakeResult) -> None:
    class _BrokenNotifier:
        def send(self, r) -> None:  # noqa: ANN001
            raise RuntimeError("boom")

    notifier = TimeoutNotifier(inner=_BrokenNotifier(), timeout_seconds=2.0)
    with pytest.raises(RuntimeError, match="boom"):
        notifier.send(result)
