"""Tests for pipewatch.notifiers.rate_limited_notifier."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.rate_limiter import RateLimiter
from pipewatch.notifiers.rate_limited_notifier import RateLimitedNotifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(name: str = "pipe_a", ok: bool = False) -> CheckResult:
    return CheckResult(
        pipeline_name=name,
        success=ok,
        error_message=None if ok else "something broke",
    )


@pytest.fixture
def inner() -> MagicMock:
    return MagicMock()


@pytest.fixture
def limiter() -> RateLimiter:
    # Very long default window so records stay fresh across the test
    return RateLimiter(db_path=":memory:", default_window_seconds=3600)


@pytest.fixture
def notifier(inner: MagicMock, limiter: RateLimiter) -> RateLimitedNotifier:
    return RateLimitedNotifier(inner, limiter)


# ---------------------------------------------------------------------------
# Forwarding behaviour
# ---------------------------------------------------------------------------

def test_send_forwards_when_not_limited(
    notifier: RateLimitedNotifier, inner: MagicMock
) -> None:
    result = _result()
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_send_records_after_forwarding(
    notifier: RateLimitedNotifier, limiter: RateLimiter
) -> None:
    notifier.send(_result("pipe_a"))
    assert limiter.is_rate_limited("pipe_a") is True


def test_second_send_is_suppressed(
    notifier: RateLimitedNotifier, inner: MagicMock
) -> None:
    notifier.send(_result("pipe_a"))
    notifier.send(_result("pipe_a"))
    # Inner notifier should only be called once
    assert inner.send.call_count == 1


def test_different_pipelines_not_suppressed(
    notifier: RateLimitedNotifier, inner: MagicMock
) -> None:
    notifier.send(_result("pipe_a"))
    notifier.send(_result("pipe_b"))
    assert inner.send.call_count == 2


# ---------------------------------------------------------------------------
# Custom per-call window
# ---------------------------------------------------------------------------

def test_custom_window_zero_never_limits(
    inner: MagicMock, limiter: RateLimiter
) -> None:
    """A window of 0 means records expire immediately — never rate-limited."""
    rln = RateLimitedNotifier(inner, limiter, window_seconds=0)
    rln.send(_result("pipe_a"))
    rln.send(_result("pipe_a"))
    assert inner.send.call_count == 2


def test_inner_exception_does_not_record(
    limiter: RateLimiter,
) -> None:
    """If the inner notifier raises, the rate-limit record must NOT be stored."""
    broken = MagicMock()
    broken.send.side_effect = RuntimeError("network error")
    rln = RateLimitedNotifier(broken, limiter)
    with pytest.raises(RuntimeError):
        rln.send(_result("pipe_a"))
    # No record should have been written
    assert limiter.is_rate_limited("pipe_a") is False
