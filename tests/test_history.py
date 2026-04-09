"""Tests for pipewatch.history.CheckHistory."""

import pytest
from pathlib import Path

from pipewatch.history import CheckHistory
from pipewatch.monitor import CheckResult


@pytest.fixture
def db(tmp_path: Path) -> CheckHistory:
    """Return a CheckHistory backed by a temporary SQLite file."""
    history = CheckHistory(db_path=tmp_path / "test_history.db")
    yield history
    history.close()


@pytest.fixture
def ok_result() -> CheckResult:
    return CheckResult(pipeline_name="etl_users", success=True, error_message=None)


@pytest.fixture
def fail_result() -> CheckResult:
    return CheckResult(pipeline_name="etl_users", success=False, error_message="Timeout after 30s")


def test_record_and_retrieve_success(db: CheckHistory, ok_result: CheckResult) -> None:
    db.record(ok_result)
    rows = db.get_recent("etl_users")
    assert len(rows) == 1
    assert rows[0]["pipeline"] == "etl_users"
    assert rows[0]["success"] is True
    assert rows[0]["error_message"] is None


def test_record_and_retrieve_failure(db: CheckHistory, fail_result: CheckResult) -> None:
    db.record(fail_result)
    rows = db.get_recent("etl_users")
    assert len(rows) == 1
    assert rows[0]["success"] is False
    assert rows[0]["error_message"] == "Timeout after 30s"


def test_get_recent_respects_limit(db: CheckHistory, ok_result: CheckResult) -> None:
    for _ in range(15):
        db.record(ok_result)
    rows = db.get_recent("etl_users", limit=5)
    assert len(rows) == 5


def test_get_recent_returns_newest_first(db: CheckHistory) -> None:
    db.record(CheckResult(pipeline_name="etl_orders", success=True, error_message=None))
    db.record(CheckResult(pipeline_name="etl_orders", success=False, error_message="err"))
    rows = db.get_recent("etl_orders")
    assert rows[0]["success"] is False  # most recent first
    assert rows[1]["success"] is True


def test_last_failure_returns_none_when_no_failures(db: CheckHistory, ok_result: CheckResult) -> None:
    db.record(ok_result)
    assert db.last_failure("etl_users") is None


def test_last_failure_returns_most_recent_failure(db: CheckHistory) -> None:
    db.record(CheckResult("pipe_x", False, "first error"))
    db.record(CheckResult("pipe_x", True, None))
    db.record(CheckResult("pipe_x", False, "latest error"))
    result = db.last_failure("pipe_x")
    assert result is not None
    assert result["error_message"] == "latest error"


def test_get_recent_unknown_pipeline_returns_empty(db: CheckHistory) -> None:
    rows = db.get_recent("nonexistent_pipeline")
    assert rows == []


def test_db_file_created(tmp_path: Path) -> None:
    db_path = tmp_path / "subdir" / "history.db"
    h = CheckHistory(db_path=db_path)
    h.close()
    assert db_path.exists()
