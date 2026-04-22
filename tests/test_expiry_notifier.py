"""Tests for ExpiryNotifier and ExpiryStore."""
from __future__ import annotations

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.expiry_notifier import ExpiryNotifier, ExpiryStore


@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool = True
    error_message: str | None = None


@pytest.fixture
def store(tmp_path):
    return ExpiryStore(db_path=str(tmp_path / "expiry.db"))


@pytest.fixture
def inner():
    return MagicMock()


@pytest.fixture
def notifier(store, inner):
    return ExpiryNotifier(inner=inner, store=store, ttl_seconds=60.0)


@pytest.fixture
def result():
    return _FakeResult(pipeline_name="pipe_a")


def test_send_forwards_first_alert(notifier, inner, result):
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_send_forwards_within_ttl(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    assert inner.send.call_count == 2


def test_send_suppressed_after_ttl_expires(store, inner, result):
    notifier = ExpiryNotifier(inner=inner, store=store, ttl_seconds=0.05)
    notifier.send(result)
    time.sleep(0.1)
    notifier.send(result)
    # Only the first send should go through
    inner.send.assert_called_once_with(result)


def test_clear_resets_expiry(store, inner, result):
    notifier = ExpiryNotifier(inner=inner, store=store, ttl_seconds=0.05)
    notifier.send(result)
    time.sleep(0.1)
    store.clear(result.pipeline_name)
    notifier.send(result)
    assert inner.send.call_count == 2


def test_invalid_ttl_raises(store, inner):
    with pytest.raises(ValueError, match="ttl_seconds"):
        ExpiryNotifier(inner=inner, store=store, ttl_seconds=0)


def test_first_sent_at_none_before_record(store):
    assert store.first_sent_at("no_such_pipe") is None


def test_record_first_sent_stores_timestamp(store):
    store.record_first_sent("pipe_b")
    ts = store.first_sent_at("pipe_b")
    assert ts is not None
    assert ts <= time.time()


def test_record_first_sent_is_idempotent(store):
    store.record_first_sent("pipe_c")
    first = store.first_sent_at("pipe_c")
    time.sleep(0.02)
    store.record_first_sent("pipe_c")  # should not overwrite
    assert store.first_sent_at("pipe_c") == first


def test_pipelines_isolated(store, inner):
    n1 = ExpiryNotifier(inner=inner, store=store, ttl_seconds=0.05)
    r1 = _FakeResult(pipeline_name="alpha")
    r2 = _FakeResult(pipeline_name="beta")
    n1.send(r1)
    time.sleep(0.1)
    n1.send(r2)  # beta not expired yet (first send)
    assert inner.send.call_count == 2
