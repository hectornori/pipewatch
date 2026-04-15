"""Tests for ArchiveNotifier and ArchiveStore."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pytest

from pipewatch.notifiers.archive_notifier import ArchiveNotifier, ArchiveStore


@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self):
        self.received: List = []

    def send(self, result) -> None:
        self.received.append(result)


@pytest.fixture
def store():
    return ArchiveStore(db_path=":memory:")


@pytest.fixture
def inner():
    return _FakeNotifier()


@pytest.fixture
def notifier(inner, store):
    return ArchiveNotifier(inner=inner, store=store)


@pytest.fixture
def result():
    return _FakeResult(pipeline_name="etl_load", success=False, error_message="timeout")


def test_send_archives_before_forwarding(notifier, store, inner, result):
    notifier.send(result)
    rows = store.get_recent("etl_load")
    assert len(rows) == 1
    assert rows[0]["pipeline"] == "etl_load"


def test_send_forwards_to_inner(notifier, inner, result):
    notifier.send(result)
    assert inner.received == [result]


def test_archive_records_failure_status(notifier, store, result):
    notifier.send(result)
    row = store.get_recent("etl_load")[0]
    assert row["success"] == 0
    assert row["error"] == "timeout"


def test_archive_records_success_status(notifier, store, inner):
    ok = _FakeResult(pipeline_name="etl_load", success=True)
    notifier.send(ok)
    row = store.get_recent("etl_load")[0]
    assert row["success"] == 1
    assert row["error"] is None


def test_get_recent_respects_limit(store):
    for i in range(10):
        store.save(_FakeResult(pipeline_name="p", success=True))
    assert len(store.get_recent("p", limit=3)) == 3


def test_get_recent_isolated_per_pipeline(store):
    store.save(_FakeResult(pipeline_name="a", success=True))
    store.save(_FakeResult(pipeline_name="b", success=False, error_message="err"))
    assert len(store.get_recent("a")) == 1
    assert len(store.get_recent("b")) == 1


def test_get_recent_empty_before_any_record(store):
    assert store.get_recent("nonexistent") == []
