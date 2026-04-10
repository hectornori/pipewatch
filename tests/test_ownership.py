"""Tests for pipewatch.ownership."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from pipewatch.ownership import OwnershipEntry, OwnershipStore


@pytest.fixture
def store() -> OwnershipStore:
    return OwnershipStore(db_path=":memory:")


@pytest.fixture
def _entry() -> OwnershipEntry:
    return OwnershipEntry(
        pipeline_name="orders-etl",
        owner="team-data-eng",
        notes="Handles nightly order aggregation",
    )


def test_get_returns_none_before_upsert(store: OwnershipStore) -> None:
    assert store.get("missing-pipeline") is None


def test_all_returns_empty_before_upsert(store: OwnershipStore) -> None:
    assert store.all() == []


def test_upsert_and_retrieve(store: OwnershipStore, _entry: OwnershipEntry) -> None:
    store.upsert(_entry)
    result = store.get(_entry.pipeline_name)
    assert result is not None
    assert result.pipeline_name == "orders-etl"
    assert result.owner == "team-data-eng"
    assert result.notes == "Handles nightly order aggregation"


def test_upsert_updates_existing(store: OwnershipStore, _entry: OwnershipEntry) -> None:
    store.upsert(_entry)
    updated = OwnershipEntry(
        pipeline_name="orders-etl",
        owner="alice@example.com",
        notes="Transferred ownership",
    )
    store.upsert(updated)
    result = store.get("orders-etl")
    assert result is not None
    assert result.owner == "alice@example.com"
    assert result.notes == "Transferred ownership"


def test_all_returns_multiple_entries(store: OwnershipStore) -> None:
    store.upsert(OwnershipEntry(pipeline_name="b-pipeline", owner="bob"))
    store.upsert(OwnershipEntry(pipeline_name="a-pipeline", owner="alice"))
    entries = store.all()
    assert len(entries) == 2
    # Should be ordered by pipeline name
    assert entries[0].pipeline_name == "a-pipeline"
    assert entries[1].pipeline_name == "b-pipeline"


def test_delete_removes_entry(store: OwnershipStore, _entry: OwnershipEntry) -> None:
    store.upsert(_entry)
    deleted = store.delete(_entry.pipeline_name)
    assert deleted is True
    assert store.get(_entry.pipeline_name) is None


def test_delete_returns_false_when_not_found(store: OwnershipStore) -> None:
    assert store.delete("nonexistent") is False


def test_updated_at_is_preserved(store: OwnershipStore) -> None:
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    entry = OwnershipEntry(pipeline_name="ts-pipeline", owner="charlie", updated_at=ts)
    store.upsert(entry)
    result = store.get("ts-pipeline")
    assert result is not None
    assert result.updated_at == ts


def test_notes_default_empty(store: OwnershipStore) -> None:
    entry = OwnershipEntry(pipeline_name="bare-pipeline", owner="dave")
    store.upsert(entry)
    result = store.get("bare-pipeline")
    assert result is not None
    assert result.notes == ""
