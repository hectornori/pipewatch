"""Tests for pipewatch.snapshot."""
from datetime import datetime

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.snapshot import PipelineSnapshot, SnapshotStore


@pytest.fixture()
def store() -> SnapshotStore:
    return SnapshotStore(db_path=":memory:")


@pytest.fixture()
def ok_result() -> CheckResult:
    return CheckResult(pipeline_name="etl_daily", success=True, error_message=None)


@pytest.fixture()
def fail_result() -> CheckResult:
    return CheckResult(
        pipeline_name="etl_daily", success=False, error_message="timeout"
    )


def test_get_returns_none_before_any_save(store: SnapshotStore) -> None:
    assert store.get("etl_daily") is None


def test_all_returns_empty_before_any_save(store: SnapshotStore) -> None:
    assert store.all() == []


def test_save_ok_result(store: SnapshotStore, ok_result: CheckResult) -> None:
    store.save(ok_result)
    snap = store.get("etl_daily")
    assert snap is not None
    assert snap.pipeline_name == "etl_daily"
    assert snap.status == "ok"
    assert snap.last_error is None


def test_save_fail_result(store: SnapshotStore, fail_result: CheckResult) -> None:
    store.save(fail_result)
    snap = store.get("etl_daily")
    assert snap is not None
    assert snap.status == "fail"
    assert snap.last_error == "timeout"


def test_save_upserts_existing_pipeline(
    store: SnapshotStore, ok_result: CheckResult, fail_result: CheckResult
) -> None:
    store.save(ok_result)
    store.save(fail_result)
    snap = store.get("etl_daily")
    assert snap is not None
    assert snap.status == "fail"
    assert snap.last_error == "timeout"


def test_all_returns_one_row_per_pipeline(store: SnapshotStore) -> None:
    store.save(CheckResult(pipeline_name="pipe_a", success=True, error_message=None))
    store.save(CheckResult(pipeline_name="pipe_b", success=False, error_message="err"))
    snaps = store.all()
    names = {s.pipeline_name for s in snaps}
    assert names == {"pipe_a", "pipe_b"}


def test_last_checked_is_datetime(store: SnapshotStore, ok_result: CheckResult) -> None:
    store.save(ok_result)
    snap = store.get("etl_daily")
    assert isinstance(snap.last_checked, datetime)


def test_snapshot_dataclass_fields() -> None:
    snap = PipelineSnapshot(
        pipeline_name="x",
        status="ok",
        last_checked=datetime(2024, 1, 1),
        last_error=None,
    )
    assert snap.pipeline_name == "x"
    assert snap.status == "ok"
    assert snap.last_error is None
