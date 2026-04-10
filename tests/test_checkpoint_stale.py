"""Tests for CheckpointStore and StaleDetector."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pipewatch.checkpoint import CheckpointStore
from pipewatch.stale_detector import StaleDetector, StalePipeline


@pytest.fixture
def store(tmp_path):
    return CheckpointStore(db_path=str(tmp_path / "checkpoints.db"))


@pytest.fixture
def detector(store):
    return StaleDetector(store=store, default_threshold_minutes=60.0)


# --- CheckpointStore ---

def test_last_success_none_before_record(store):
    assert store.last_success_at("pipe_a") is None


def test_minutes_since_success_none_before_record(store):
    assert store.minutes_since_success("pipe_a") is None


def test_record_and_retrieve(store):
    ts = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    store.record_success("pipe_a", ts=ts)
    assert store.last_success_at("pipe_a") == ts


def test_record_updates_existing(store):
    ts1 = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    ts2 = datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc)
    store.record_success("pipe_a", ts=ts1)
    store.record_success("pipe_a", ts=ts2)
    assert store.last_success_at("pipe_a") == ts2


def test_clear_removes_record(store):
    store.record_success("pipe_a")
    store.clear("pipe_a")
    assert store.last_success_at("pipe_a") is None


def test_minutes_since_success_is_small_for_recent(store):
    store.record_success("pipe_a")  # defaults to now
    elapsed = store.minutes_since_success("pipe_a")
    assert elapsed is not None
    assert elapsed < 1.0


# --- StaleDetector ---

def test_stale_when_never_run(detector):
    result = detector.check("pipe_b")
    assert isinstance(result, StalePipeline)
    assert result.minutes_since_success is None


def test_not_stale_when_recent(store, detector):
    store.record_success("pipe_c")  # just now
    result = detector.check("pipe_c")
    assert result is None


def test_stale_when_old(store, detector):
    old_ts = datetime.now(timezone.utc) - timedelta(minutes=120)
    store.record_success("pipe_d", ts=old_ts)
    result = detector.check("pipe_d", threshold_minutes=60.0)
    assert isinstance(result, StalePipeline)
    assert result.minutes_since_success is not None
    assert result.minutes_since_success > 60.0


def test_check_all_returns_only_stale(store, detector):
    store.record_success("fresh")  # just now
    old_ts = datetime.now(timezone.utc) - timedelta(minutes=120)
    store.record_success("old", ts=old_ts)
    stale = detector.check_all(["fresh", "old", "never"])
    stale_names = {s.name for s in stale}
    assert "fresh" not in stale_names
    assert "old" in stale_names
    assert "never" in stale_names


def test_stale_reason_no_record(detector):
    sp = StalePipeline(name="p", minutes_since_success=None, threshold_minutes=60)
    assert "no successful run" in sp.reason


def test_stale_reason_with_elapsed(detector):
    sp = StalePipeline(name="p", minutes_since_success=90.5, threshold_minutes=60)
    assert "90.5" in sp.reason
    assert "60" in sp.reason
