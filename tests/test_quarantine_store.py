"""Unit tests for QuarantineStore in isolation."""
from __future__ import annotations

import pytest

from pipewatch.notifiers.quarantine_notifier import QuarantineStore


@pytest.fixture
def store(tmp_path):
    return QuarantineStore(db_path=str(tmp_path / "qs.db"))


def test_not_quarantined_before_any_record(store):
    assert not store.is_quarantined("pipe_x")


def test_record_failure_returns_count(store):
    count = store.record_failure("pipe_x")
    assert count == 1


def test_record_failure_increments(store):
    store.record_failure("pipe_x")
    store.record_failure("pipe_x")
    count = store.record_failure("pipe_x")
    assert count == 3


def test_quarantine_marks_pipeline(store):
    store.record_failure("pipe_x")
    store.quarantine("pipe_x")
    assert store.is_quarantined("pipe_x")


def test_clear_removes_quarantine(store):
    store.record_failure("pipe_x")
    store.quarantine("pipe_x")
    store.clear("pipe_x")
    assert not store.is_quarantined("pipe_x")


def test_clear_resets_failure_count(store):
    store.record_failure("pipe_x")
    store.record_failure("pipe_x")
    store.clear("pipe_x")
    count = store.record_failure("pipe_x")
    assert count == 1


def test_pipelines_isolated(store):
    store.record_failure("pipe_a")
    store.quarantine("pipe_a")
    assert not store.is_quarantined("pipe_b")


def test_clear_on_unknown_pipeline_is_safe(store):
    store.clear("never_seen")  # should not raise
    assert not store.is_quarantined("never_seen")
