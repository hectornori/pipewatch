"""Tests for CircuitBreakerNotifier."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, call

import pytest

from pipewatch.notifiers.circuit_breaker_notifier import CircuitBreakerNotifier


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

class _FakeResult:
    pipeline_name = "test_pipe"
    success = False
    error_message = "boom"


@pytest.fixture()
def inner():
    return MagicMock()


@pytest.fixture()
def notifier(inner):
    return CircuitBreakerNotifier(inner=inner, failure_threshold=3, recovery_timeout=60.0)


# ------------------------------------------------------------------ #
# Tests                                                               #
# ------------------------------------------------------------------ #

def test_send_forwards_when_closed(notifier, inner):
    result = _FakeResult()
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_state_closed_initially(notifier):
    assert notifier.state == "closed"
    assert not notifier.is_open


def test_consecutive_failures_increment(notifier, inner):
    inner.send.side_effect = RuntimeError("fail")
    for _ in range(2):
        with pytest.raises(RuntimeError):
            notifier.send(_FakeResult())
    assert notifier._consecutive_failures == 2
    assert notifier.state == "closed"


def test_circuit_opens_at_threshold(notifier, inner):
    inner.send.side_effect = RuntimeError("fail")
    for _ in range(3):
        with pytest.raises(RuntimeError):
            notifier.send(_FakeResult())
    assert notifier.state == "open"
    assert notifier.is_open


def test_send_suppressed_when_open(notifier, inner):
    inner.send.side_effect = RuntimeError("fail")
    for _ in range(3):
        with pytest.raises(RuntimeError):
            notifier.send(_FakeResult())

    # Reset side-effect so a real send would succeed
    inner.send.side_effect = None
    notifier.send(_FakeResult())  # should be suppressed, no exception
    # inner.send was called exactly 3 times (the failures), not a 4th
    assert inner.send.call_count == 3


def test_circuit_half_open_after_recovery_timeout(notifier, inner):
    inner.send.side_effect = RuntimeError("fail")
    for _ in range(3):
        with pytest.raises(RuntimeError):
            notifier.send(_FakeResult())

    # Simulate recovery timeout elapsed
    notifier._opened_at -= 61.0  # type: ignore[operator]
    assert notifier.state == "half-open"
    assert not notifier.is_open


def test_successful_send_resets_failures(notifier, inner):
    inner.send.side_effect = [RuntimeError("fail"), RuntimeError("fail"), None]
    for i in range(2):
        with pytest.raises(RuntimeError):
            notifier.send(_FakeResult())
    assert notifier._consecutive_failures == 2

    inner.send.side_effect = None
    notifier.send(_FakeResult())
    assert notifier._consecutive_failures == 0
    assert notifier._opened_at is None


def test_reset_closes_circuit(notifier, inner):
    inner.send.side_effect = RuntimeError("fail")
    for _ in range(3):
        with pytest.raises(RuntimeError):
            notifier.send(_FakeResult())
    assert notifier.is_open

    notifier.reset()
    assert notifier.state == "closed"
    assert notifier._consecutive_failures == 0
