"""Tests for pipewatch.runbook."""
from datetime import datetime, timezone

import pytest

from pipewatch.runbook import RunbookEntry, RunbookStore


@pytest.fixture()
def store() -> RunbookStore:
    return RunbookStore(db_path=":memory:")


def _entry(
    name: str = "pipeline_a",
    url: str = "https://wiki.example.com/runbook",
    description: str = "Fix guide",
) -> RunbookEntry:
    return RunbookEntry(pipeline_name=name, url=url, description=description)


def test_get_returns_none_before_upsert(store: RunbookStore) -> None:
    assert store.get("missing") is None


def test_all_returns_empty_before_upsert(store: RunbookStore) -> None:
    assert store.all() == []


def test_upsert_and_retrieve(store: RunbookStore) -> None:
    entry = _entry()
    store.upsert(entry)
    result = store.get("pipeline_a")
    assert result is not None
    assert result.pipeline_name == "pipeline_a"
    assert result.url == "https://wiki.example.com/runbook"
    assert result.description == "Fix guide"


def test_upsert_overwrites_existing(store: RunbookStore) -> None:
    store.upsert(_entry(url="https://old.example.com"))
    store.upsert(_entry(url="https://new.example.com", description="Updated"))
    result = store.get("pipeline_a")
    assert result is not None
    assert result.url == "https://new.example.com"
    assert result.description == "Updated"


def test_all_returns_all_entries(store: RunbookStore) -> None:
    store.upsert(_entry(name="alpha"))
    store.upsert(_entry(name="beta"))
    store.upsert(_entry(name="gamma"))
    entries = store.all()
    assert len(entries) == 3
    assert [e.pipeline_name for e in entries] == ["alpha", "beta", "gamma"]


def test_delete_existing_entry(store: RunbookStore) -> None:
    store.upsert(_entry())
    deleted = store.delete("pipeline_a")
    assert deleted is True
    assert store.get("pipeline_a") is None


def test_delete_nonexistent_returns_false(store: RunbookStore) -> None:
    assert store.delete("ghost") is False


def test_format_for_alert_with_description(store: RunbookStore) -> None:
    store.upsert(_entry(url="https://wiki.example.com/fix", description="Fix guide"))
    text = store.format_for_alert("pipeline_a")
    assert "https://wiki.example.com/fix" in text
    assert "Fix guide" in text


def test_format_for_alert_without_description(store: RunbookStore) -> None:
    store.upsert(_entry(url="https://wiki.example.com/fix", description=""))
    text = store.format_for_alert("pipeline_a")
    assert text == "Runbook: https://wiki.example.com/fix"


def test_format_for_alert_missing_pipeline(store: RunbookStore) -> None:
    assert store.format_for_alert("nonexistent") == ""


def test_updated_at_is_preserved(store: RunbookStore) -> None:
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    entry = RunbookEntry(pipeline_name="p", url="https://x.com", updated_at=ts)
    store.upsert(entry)
    result = store.get("p")
    assert result is not None
    assert result.updated_at == ts
