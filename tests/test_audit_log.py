"""Tests for AuditLog persistence and retrieval."""
import pytest
from datetime import timezone

from pipewatch.audit_log import AuditLog


@pytest.fixture
def log(tmp_path):
    return AuditLog(db_path=str(tmp_path / "audit.db"))


def test_get_recent_empty_before_any_record(log):
    assert log.get_recent("pipe_a") == []


def test_get_all_empty_before_any_record(log):
    assert log.get_all() == []


def test_record_stores_entry(log):
    log.record("check", "pipe_a", "ok=True")
    entries = log.get_recent("pipe_a")
    assert len(entries) == 1
    e = entries[0]
    assert e.event_type == "check"
    assert e.pipeline_name == "pipe_a"
    assert e.detail == "ok=True"
    assert e.ts.tzinfo == timezone.utc


def test_get_recent_filters_by_pipeline(log):
    log.record("check", "pipe_a", "ok=True")
    log.record("alert", "pipe_b", "sent")
    assert len(log.get_recent("pipe_a")) == 1
    assert len(log.get_recent("pipe_b")) == 1


def test_get_all_returns_all_pipelines(log):
    log.record("check", "pipe_a", "ok=True")
    log.record("alert", "pipe_b", "sent")
    assert len(log.get_all()) == 2


def test_get_recent_respects_limit(log):
    for i in range(10):
        log.record("check", "pipe_a", f"run={i}")
    entries = log.get_recent("pipe_a", limit=3)
    assert len(entries) == 3


def test_multiple_event_types_stored(log):
    log.record("check", "pipe_a", "ok=True")
    log.record("mute", "pipe_a", "muted for 30 min")
    log.record("escalation", "pipe_a", "escalated to on-call")
    entries = log.get_recent("pipe_a")
    event_types = {e.event_type for e in entries}
    assert event_types == {"check", "mute", "escalation"}


def test_entries_ordered_by_ts_descending(log):
    for i in range(5):
        log.record("check", "pipe_a", f"run={i}")
    entries = log.get_recent("pipe_a")
    timestamps = [e.ts for e in entries]
    assert timestamps == sorted(timestamps, reverse=True)
