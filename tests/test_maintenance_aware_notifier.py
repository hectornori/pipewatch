"""Tests for pipewatch.notifiers.maintenance_aware_notifier."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from pipewatch.maintenance_window import MaintenanceStore, MaintenanceWindow
from pipewatch.monitor import CheckResult
from pipewatch.notifiers.maintenance_aware_notifier import MaintenanceAwareNotifier


def _result(pipeline: str = "pipe_a", success: bool = True) -> CheckResult:
    return CheckResult(
        pipeline_name=pipeline,
        success=success,
        error_message=None if success else "boom",
    )


def _active_window(pipeline: str = "pipe_a") -> MaintenanceWindow:
    now = datetime.utcnow()
    return MaintenanceWindow(
        pipeline_name=pipeline,
        start=now - timedelta(minutes=5),
        end=now + timedelta(minutes=5),
    )


@pytest.fixture()
def store() -> MaintenanceStore:
    return MaintenanceStore(db_path=":memory:")


@pytest.fixture()
def inner() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def notifier(inner, store) -> MaintenanceAwareNotifier:
    return MaintenanceAwareNotifier(inner=inner, store=store)


def test_send_forwards_when_no_maintenance(notifier, inner, store):
    result = _result("pipe_a", success=False)
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_send_suppressed_during_maintenance(notifier, inner, store):
    store.add(_active_window("pipe_a"))
    result = _result("pipe_a", success=False)
    notifier.send(result)
    inner.send.assert_not_called()


def test_send_forwards_for_different_pipeline(notifier, inner, store):
    store.add(_active_window("pipe_a"))
    result = _result("pipe_b", success=False)
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_send_forwards_after_window_expires(inner, store):
    past_window = MaintenanceWindow(
        pipeline_name="pipe_a",
        start=datetime.utcnow() - timedelta(minutes=30),
        end=datetime.utcnow() - timedelta(minutes=10),
    )
    store.add(past_window)
    notifier = MaintenanceAwareNotifier(inner=inner, store=store)
    result = _result("pipe_a", success=False)
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_send_suppresses_success_too_during_maintenance(notifier, inner, store):
    """Even successful results are silenced — maintenance means no noise."""
    store.add(_active_window("pipe_a"))
    result = _result("pipe_a", success=True)
    notifier.send(result)
    inner.send.assert_not_called()
