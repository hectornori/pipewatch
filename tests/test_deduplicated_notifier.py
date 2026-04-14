"""Tests for DeduplicatedNotifier."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.deduplication import DeduplicationStore
from pipewatch.monitor import CheckResult
from pipewatch.notifiers.deduplicated_notifier import DeduplicatedNotifier


@pytest.fixture()
def store(tmp_path):
    return DeduplicationStore(db_path=str(tmp_path / "dedup.db"))


@pytest.fixture()
def inner():
    return MagicMock()


@pytest.fixture()
def notifier(inner, store):
    return DeduplicatedNotifier(inner=inner, store=store, ttl_seconds=60)


@pytest.fixture()
def _result():
    return CheckResult(pipeline_name="pipe_a", success=False, error_message="boom")


def test_send_forwards_first_alert(notifier, inner, _result):
    notifier.send(_result)
    inner.send.assert_called_once_with(_result)


def test_send_suppresses_duplicate(notifier, inner, _result):
    notifier.send(_result)
    notifier.send(_result)
    assert inner.send.call_count == 1


def test_send_forwards_different_error(notifier, inner):
    r1 = CheckResult(pipeline_name="pipe_a", success=False, error_message="err1")
    r2 = CheckResult(pipeline_name="pipe_a", success=False, error_message="err2")
    notifier.send(r1)
    notifier.send(r2)
    assert inner.send.call_count == 2


def test_send_forwards_different_pipeline(notifier, inner):
    r1 = CheckResult(pipeline_name="pipe_a", success=False, error_message="boom")
    r2 = CheckResult(pipeline_name="pipe_b", success=False, error_message="boom")
    notifier.send(r1)
    notifier.send(r2)
    assert inner.send.call_count == 2


def test_expired_duplicate_is_forwarded(inner, store, _result):
    notifier = DeduplicatedNotifier(inner=inner, store=store, ttl_seconds=0)
    # ttl=0 means every alert is treated as expired immediately
    notifier.send(_result)
    notifier.send(_result)
    assert inner.send.call_count == 2


def test_invalid_ttl_raises():
    with pytest.raises(ValueError, match="ttl_seconds"):
        DeduplicatedNotifier(
            inner=MagicMock(),
            store=MagicMock(),
            ttl_seconds=-1,
        )


def test_send_success_result_forwarded(notifier, inner):
    result = CheckResult(pipeline_name="pipe_a", success=True, error_message=None)
    notifier.send(result)
    inner.send.assert_called_once_with(result)
