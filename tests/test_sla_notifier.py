"""Tests for pipewatch.notifiers.sla_notifier."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.notifiers.sla_notifier import SLANotifier
from pipewatch.sla_tracker import SLATracker


def _utc(**kwargs) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**kwargs)


@pytest.fixture
def tracker(tmp_path):
    return SLATracker(db_path=str(tmp_path / "sla.db"))


@pytest.fixture
def inner():
    return MagicMock()


@pytest.fixture
def notifier(inner, tracker):
    return SLANotifier(inner=inner, tracker=tracker)


def _result(name="pipe_a", success=True, error=None):
    return CheckResult(pipeline_name=name, success=success, error_message=error)


# ---------------------------------------------------------------------------

def test_forwards_when_no_sla_registered(notifier, inner):
    result = _result()
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_forwards_when_sla_not_breached(notifier, inner, tracker):
    tracker.register("pipe_a", expected_by=_utc(hours=1))
    result = _result()
    notifier.send(result)
    inner.send.assert_called_once()
    sent = inner.send.call_args[0][0]
    # No SLA annotation expected
    assert "[SLA]" not in (sent.error_message or "")


def test_clears_sla_after_send(notifier, tracker):
    tracker.register("pipe_a", expected_by=_utc(hours=1))
    notifier.send(_result())
    # Window should be cleared
    assert tracker.check_breach("pipe_a") is None


def test_augments_error_message_on_breach(notifier, inner, tracker):
    tracker.register("pipe_a", expected_by=_utc(minutes=-30))
    result = _result(error="Command failed")
    notifier.send(result)
    inner.send.assert_called_once()
    sent = inner.send.call_args[0][0]
    assert "[SLA]" in sent.error_message
    assert "pipe_a" in sent.error_message
    assert "Command failed" in sent.error_message


def test_breach_clears_sla_entry(notifier, tracker):
    tracker.register("pipe_a", expected_by=_utc(minutes=-5))
    notifier.send(_result())
    assert tracker.check_breach("pipe_a") is None


def test_no_sla_breach_preserves_original_error(notifier, inner, tracker):
    tracker.register("pipe_a", expected_by=_utc(hours=2))
    result = _result(error="Some error")
    notifier.send(result)
    sent = inner.send.call_args[0][0]
    assert sent.error_message == "Some error"
