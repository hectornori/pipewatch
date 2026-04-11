"""Tests for FallbackNotifier."""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.notifiers.fallback_notifier import FallbackNotifier


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _result() -> CheckResult:
    return CheckResult(pipeline_name="etl_daily", success=False, error_message="boom")


@pytest.fixture()
def primary() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def fallback() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def notifier(primary: MagicMock, fallback: MagicMock) -> FallbackNotifier:
    return FallbackNotifier(primary=primary, fallback=fallback)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_primary_called_first(_result, notifier, primary, fallback):
    notifier.send(_result)
    primary.send.assert_called_once_with(_result)


def test_fallback_not_called_when_primary_succeeds(_result, notifier, primary, fallback):
    notifier.send(_result)
    fallback.send.assert_not_called()


def test_fallback_called_when_primary_raises(_result, notifier, primary, fallback):
    primary.send.side_effect = RuntimeError("slack down")
    notifier.send(_result)
    fallback.send.assert_called_once_with(_result)


def test_no_exception_raised_when_primary_raises_but_fallback_succeeds(
    _result, notifier, primary, fallback
):
    primary.send.side_effect = RuntimeError("slack down")
    # fallback succeeds by default (no side_effect set)
    notifier.send(_result)  # should not raise


def test_exception_raised_when_both_fail(_result, notifier, primary, fallback):
    primary.send.side_effect = RuntimeError("slack down")
    fallback.send.side_effect = OSError("smtp error")
    with pytest.raises(OSError, match="smtp error"):
        notifier.send(_result)


def test_fallback_exception_chains_primary(_result, notifier, primary, fallback):
    primary_exc = RuntimeError("primary broke")
    fallback_exc = OSError("fallback broke")
    primary.send.side_effect = primary_exc
    fallback.send.side_effect = fallback_exc
    with pytest.raises(OSError) as exc_info:
        notifier.send(_result)
    assert exc_info.value.__cause__ is primary_exc


def test_send_order_primary_before_fallback(_result, primary, fallback):
    """Verify call ordering via a shared call recorder."""
    manager = MagicMock()
    manager.attach_mock(primary, "primary")
    manager.attach_mock(fallback, "fallback")
    FallbackNotifier(primary=primary, fallback=fallback).send(_result)
    assert manager.mock_calls == [call.primary.send(_result)]
