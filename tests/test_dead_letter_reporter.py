"""Tests for dead_letter_reporter."""
from __future__ import annotations

import pytest
from pipewatch.notifiers.dead_letter_notifier import DeadLetterStore
from pipewatch.dead_letter_reporter import build_dead_letter_table


@pytest.fixture
def store() -> DeadLetterStore:
    return DeadLetterStore(db_path=":memory:")


def test_empty_store_returns_message(store):
    result = build_dead_letter_table(store)
    assert result == "No dead-letter entries."


def test_table_contains_pipeline_name(store):
    store.record(pipeline="my_pipe", error="timeout", payload="...")
    table = build_dead_letter_table(store)
    assert "my_pipe" in table


def test_table_contains_error(store):
    store.record(pipeline="pipe_x", error="connection refused", payload="...")
    table = build_dead_letter_table(store)
    assert "connection refused" in table


def test_table_has_header(store):
    store.record(pipeline="p", error="e", payload="x")
    table = build_dead_letter_table(store)
    assert "Pipeline" in table
    assert "Error" in table
    assert "Recorded At" in table


def test_long_error_is_truncated(store):
    long_error = "x" * 200
    store.record(pipeline="p", error=long_error, payload="")
    table = build_dead_letter_table(store)
    assert "…" in table


def test_multiple_entries_all_shown(store):
    store.record(pipeline="alpha", error="err1", payload="")
    store.record(pipeline="beta", error="err2", payload="")
    table = build_dead_letter_table(store)
    assert "alpha" in table
    assert "beta" in table
