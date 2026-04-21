"""Tests for MuteAwareNotifier."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from pipewatch.mute_manager import MuteManager
from pipewatch.notifiers.mute_aware_notifier import MuteAwareNotifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, pipeline_name: str, success: bool = True):
        self.pipeline_name = pipeline_name
        self.success = success
        self.error_message: str | None = None


class _NoNameResult:
    """Result without a pipeline_name attribute."""
    success = True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def manager(tmp_path):
    return MuteManager(db_path=str(tmp_path / "mute.db"))


@pytest.fixture()
def inner():
    m = MagicMock()
    m.send = MagicMock()
    return m


@pytest.fixture()
def notifier(inner, manager):
    return MuteAwareNotifier(inner=inner, mute_manager=manager)


@pytest.fixture()
def result():
    return _FakeResult(pipeline_name="pipe_a")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_forwards_when_not_muted(notifier, inner, result):
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_suppresses_when_muted(notifier, inner, manager, result):
    future = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    manager.mute("pipe_a", until=future)

    notifier.send(result)

    inner.send.assert_not_called()


def test_forwards_after_mute_expires(notifier, inner, manager, result):
    past = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    manager.mute("pipe_a", until=past)

    notifier.send(result)

    inner.send.assert_called_once_with(result)


def test_forwards_different_pipeline_when_one_muted(notifier, inner, manager):
    future = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    manager.mute("pipe_a", until=future)

    other = _FakeResult(pipeline_name="pipe_b")
    notifier.send(other)

    inner.send.assert_called_once_with(other)


def test_forwards_result_without_pipeline_name(notifier, inner):
    result = _NoNameResult()
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_unmute_restores_forwarding(notifier, inner, manager, result):
    future = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    manager.mute("pipe_a", until=future)
    manager.unmute("pipe_a")

    notifier.send(result)

    inner.send.assert_called_once_with(result)
