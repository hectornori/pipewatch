"""Tests for ThrottleStore."""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta

import pytest

from pipewatch.throttle import ThrottleStore


@pytest.fixture
def store(tmp_path):
    return ThrottleStore(db_path=str(tmp_path / "throttle.db"))


def test_last_sent_at_none_before_record(store):
    assert store.last_sent_at("pipe_a", "slack") is None


def test_not_throttled_when_no_record(store):
    assert store.is_throttled("pipe_a", "slack", 300) is False


def test_record_stores_timestamp(store):
    store.record("pipe_a", "slack")
    ts = store.last_sent_at("pipe_a", "slack")
    assert ts is not None
    assert isinstance(ts, datetime)
    assert ts.tzinfo is not None


def test_throttled_immediately_after_record(store):
    store.record("pipe_a", "slack")
    assert store.is_throttled("pipe_a", "slack", 300) is True


def test_not_throttled_when_interval_zero(store):
    store.record("pipe_a", "slack")
    # zero-second interval means never throttle
    assert store.is_throttled("pipe_a", "slack", 0) is False


def test_not_throttled_for_different_channel(store):
    store.record("pipe_a", "slack")
    assert store.is_throttled("pipe_a", "email", 300) is False


def test_not_throttled_for_different_pipeline(store):
    store.record("pipe_a", "slack")
    assert store.is_throttled("pipe_b", "slack", 300) is False


def test_record_upserts_on_repeat(store):
    store.record("pipe_a", "slack")
    first = store.last_sent_at("pipe_a", "slack")
    time.sleep(0.05)
    store.record("pipe_a", "slack")
    second = store.last_sent_at("pipe_a", "slack")
    assert second >= first  # type: ignore[operator]


def test_clear_removes_record(store):
    store.record("pipe_a", "slack")
    store.clear("pipe_a", "slack")
    assert store.last_sent_at("pipe_a", "slack") is None
    assert store.is_throttled("pipe_a", "slack", 300) is False


def test_clear_noop_when_no_record(store):
    # Should not raise
    store.clear("pipe_x", "slack")
