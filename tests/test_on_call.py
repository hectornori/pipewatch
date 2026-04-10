"""Tests for pipewatch.on_call."""

from datetime import datetime, timedelta, timezone

import pytest

from pipewatch.on_call import OnCallEntry, OnCallStore


UTC = timezone.utc


@pytest.fixture()
def store() -> OnCallStore:
    return OnCallStore(db_path=":memory:")


def _entry(
    name: str = "Alice",
    contact: str = "alice@example.com",
    offset_hours: int = -1,
    duration_hours: int = 8,
) -> OnCallEntry:
    now = datetime.now(UTC)
    return OnCallEntry(
        name=name,
        contact=contact,
        start_utc=now + timedelta(hours=offset_hours),
        end_utc=now + timedelta(hours=offset_hours + duration_hours),
    )


# --- OnCallEntry.is_active ---

def test_entry_is_active_during_window():
    e = _entry(offset_hours=-1, duration_hours=8)
    assert e.is_active() is True


def test_entry_not_active_before_window():
    now = datetime.now(UTC)
    e = OnCallEntry(
        name="Bob",
        contact="bob@example.com",
        start_utc=now + timedelta(hours=2),
        end_utc=now + timedelta(hours=10),
    )
    assert e.is_active() is False


def test_entry_not_active_after_window():
    now = datetime.now(UTC)
    e = OnCallEntry(
        name="Carol",
        contact="carol@example.com",
        start_utc=now - timedelta(hours=10),
        end_utc=now - timedelta(hours=2),
    )
    assert e.is_active() is False


# --- OnCallStore ---

def test_current_returns_none_when_empty(store):
    assert store.current() is None


def test_all_entries_empty_initially(store):
    assert store.all_entries() == []


def test_add_and_retrieve_current(store):
    e = _entry(name="Dave", contact="dave@example.com")
    store.add(e)
    result = store.current()
    assert result is not None
    assert result.name == "Dave"
    assert result.contact == "dave@example.com"


def test_current_returns_none_for_future_entry(store):
    now = datetime.now(UTC)
    future = OnCallEntry(
        name="Eve",
        contact="eve@example.com",
        start_utc=now + timedelta(hours=5),
        end_utc=now + timedelta(hours=13),
    )
    store.add(future)
    assert store.current() is None


def test_all_entries_returns_all_added(store):
    store.add(_entry(name="Alice", contact="a@example.com", offset_hours=-8, duration_hours=8))
    store.add(_entry(name="Bob", contact="b@example.com", offset_hours=0, duration_hours=8))
    entries = store.all_entries()
    assert len(entries) == 2
    names = [e.name for e in entries]
    assert "Alice" in names
    assert "Bob" in names


def test_current_picks_most_recent_overlapping_entry(store):
    now = datetime.now(UTC)
    older = OnCallEntry(
        name="Old",
        contact="old@example.com",
        start_utc=now - timedelta(hours=4),
        end_utc=now + timedelta(hours=4),
    )
    newer = OnCallEntry(
        name="New",
        contact="new@example.com",
        start_utc=now - timedelta(hours=1),
        end_utc=now + timedelta(hours=7),
    )
    store.add(older)
    store.add(newer)
    result = store.current()
    assert result is not None
    assert result.name == "New"
