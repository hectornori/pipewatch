"""Tests for RetryNotifier."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.retry import RetryPolicy
from pipewatch.notifiers.retry_notifier import RetryNotifier, retry_notifier_from_dict


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _result() -> CheckResult:
    return CheckResult(pipeline_name="pipe", success=False, error_message="boom")


@pytest.fixture()
def inner() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def notifier(inner: MagicMock) -> RetryNotifier:
    policy = RetryPolicy(max_attempts=3, delay_seconds=0.0, backoff=1.0)
    return RetryNotifier(inner=inner, policy=policy)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_send_forwards_on_success(notifier: RetryNotifier, inner: MagicMock, _result: CheckResult) -> None:
    notifier.send(_result)
    inner.send.assert_called_once_with(_result)


def test_send_retries_on_transient_failure(inner: MagicMock, _result: CheckResult) -> None:
    inner.send.side_effect = [RuntimeError("transient"), None]
    policy = RetryPolicy(max_attempts=3, delay_seconds=0.0, backoff=1.0)
    notifier = RetryNotifier(inner=inner, policy=policy)

    notifier.send(_result)

    assert inner.send.call_count == 2


def test_send_raises_after_all_attempts_exhausted(inner: MagicMock, _result: CheckResult) -> None:
    inner.send.side_effect = RuntimeError("always fails")
    policy = RetryPolicy(max_attempts=2, delay_seconds=0.0, backoff=1.0)
    notifier = RetryNotifier(inner=inner, policy=policy)

    with pytest.raises(RuntimeError, match="always fails"):
        notifier.send(_result)

    assert inner.send.call_count == 2


def test_default_policy_used_when_none_provided(inner: MagicMock, _result: CheckResult) -> None:
    notifier = RetryNotifier(inner=inner)
    notifier.send(_result)
    inner.send.assert_called_once_with(_result)


def test_retry_notifier_from_dict_builds_correctly(inner: MagicMock, _result: CheckResult) -> None:
    cfg = {"max_attempts": 2, "delay_seconds": 0.0, "backoff": 1.0}
    notifier = retry_notifier_from_dict(inner=inner, cfg=cfg)
    notifier.send(_result)
    inner.send.assert_called_once_with(_result)


def test_retry_notifier_from_dict_respects_attempts(inner: MagicMock, _result: CheckResult) -> None:
    inner.send.side_effect = ValueError("nope")
    cfg = {"max_attempts": 3, "delay_seconds": 0.0, "backoff": 1.0}
    notifier = retry_notifier_from_dict(inner=inner, cfg=cfg)

    with pytest.raises(ValueError):
        notifier.send(_result)

    assert inner.send.call_count == 3
