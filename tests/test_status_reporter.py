"""Tests for pipewatch.status_reporter."""
from datetime import datetime

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.snapshot import SnapshotStore
from pipewatch.status_reporter import build_status_table


@pytest.fixture()
def populated_store() -> SnapshotStore:
    store = SnapshotStore(db_path=":memory:")
    store.save(CheckResult(pipeline_name="pipe_ok", success=True, error_message=None))
    store.save(
        CheckResult(pipeline_name="pipe_fail", success=False, error_message="boom")
    )
    return store


def test_table_contains_pipeline_names(populated_store: SnapshotStore) -> None:
    table = build_status_table(populated_store, ["pipe_ok", "pipe_fail"])
    assert "pipe_ok" in table
    assert "pipe_fail" in table


def test_table_shows_ok_status(populated_store: SnapshotStore) -> None:
    table = build_status_table(populated_store, ["pipe_ok"])
    assert "OK" in table


def test_table_shows_fail_status(populated_store: SnapshotStore) -> None:
    table = build_status_table(populated_store, ["pipe_fail"])
    assert "FAIL" in table


def test_table_shows_error_message(populated_store: SnapshotStore) -> None:
    table = build_status_table(populated_store, ["pipe_fail"])
    assert "boom" in table


def test_unknown_pipeline_shows_unknown(populated_store: SnapshotStore) -> None:
    table = build_status_table(populated_store, ["pipe_missing"])
    assert "UNKNOWN" in table
    assert "pipe_missing" in table


def test_empty_pipeline_list_returns_header_only() -> None:
    store = SnapshotStore(db_path=":memory:")
    table = build_status_table(store, [])
    # No rows — only header + separator
    lines = [l for l in table.splitlines() if l.strip()]
    assert len(lines) == 2


def test_dash_shown_for_no_error(populated_store: SnapshotStore) -> None:
    table = build_status_table(populated_store, ["pipe_ok"])
    # The error column for a passing pipeline should show '-'
    lines = [l for l in table.splitlines() if "pipe_ok" in l]
    assert len(lines) == 1
    assert lines[0].endswith("-")


def test_multiple_pipelines_multiple_rows(populated_store: SnapshotStore) -> None:
    table = build_status_table(populated_store, ["pipe_ok", "pipe_fail", "pipe_new"])
    data_lines = table.splitlines()[2:]  # skip header + separator
    assert len(data_lines) == 3
