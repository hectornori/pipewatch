"""Tests for ReplayNotifier and ReplayConfig."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import List
from unittest.mock import MagicMock, call

import pytest

from pipewatch.notifiers.dead_letter_notifier import DeadLetterStore, DeadLetterEntry
from pipewatch.notifiers.replay_notifier import ReplayNotifier, ReplaySummary
from pipewatch.replay_config import ReplayConfig, replay_config_from_dict


# ---------------------------------------------------------------------------
# Minimal fake result
# ---------------------------------------------------------------------------

@dataclass
class _FakeResult:
    pipeline: str = "pipe-a"
    success: bool = True
    error_message: str | None = None
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    db_path = str(tmp_path / "dl.db")
    return DeadLetterStore(db_path=db_path)


@pytest.fixture()
def inner():
    return MagicMock()


@pytest.fixture()
def notifier(inner, store):
    return ReplayNotifier(inner=inner, store=store, max_entries=10)


# ---------------------------------------------------------------------------
# ReplayConfig tests
# ---------------------------------------------------------------------------

def test_default_config_values():
    cfg = ReplayConfig()
    assert cfg.enabled is True
    assert cfg.max_entries == 50
    assert cfg.db_path == "pipewatch_dead_letters.db"


def test_invalid_max_entries_raises():
    with pytest.raises(ValueError, match="max_entries"):
        ReplayConfig(max_entries=0)


def test_empty_db_path_raises():
    with pytest.raises(ValueError, match="db_path"):
        ReplayConfig(db_path="")


def test_replay_config_from_dict():
    cfg = replay_config_from_dict({"enabled": False, "max_entries": 5, "extra": "ignored"})
    assert cfg.enabled is False
    assert cfg.max_entries == 5


# ---------------------------------------------------------------------------
# ReplaySummary tests
# ---------------------------------------------------------------------------

def test_summary_counts():
    s = ReplaySummary(succeeded=["a", "b"], failed=["c"])
    assert s.total == 3
    assert s.success_count == 2
    assert s.failure_count == 1


# ---------------------------------------------------------------------------
# ReplayNotifier.replay tests
# ---------------------------------------------------------------------------

def test_replay_empty_store_returns_empty_summary(notifier, inner):
    summary = notifier.replay()
    assert summary.total == 0
    inner.send.assert_not_called()


def test_replay_delivers_pending_entries(notifier, store, inner):
    result = _FakeResult(pipeline="pipe-a")
    store.record(result, error="timeout")

    summary = notifier.replay()

    assert summary.success_count == 1
    assert summary.failure_count == 0
    inner.send.assert_called_once()


def test_replay_marks_entry_replayed(notifier, store, inner):
    result = _FakeResult(pipeline="pipe-b")
    store.record(result, error="conn error")

    notifier.replay()
    # After successful replay the store should have no more pending entries
    remaining = store.get_pending(limit=10)
    assert remaining == []


def test_replay_leaves_entry_on_inner_failure(notifier, store, inner):
    inner.send.side_effect = RuntimeError("still broken")
    result = _FakeResult(pipeline="pipe-c")
    store.record(result, error="original error")

    summary = notifier.replay()

    assert summary.failure_count == 1
    assert summary.success_count == 0
    remaining = store.get_pending(limit=10)
    assert len(remaining) == 1


def test_replay_respects_max_entries(store, inner):
    notifier = ReplayNotifier(inner=inner, store=store, max_entries=2)
    for i in range(5):
        store.record(_FakeResult(pipeline=f"pipe-{i}"), error="err")

    summary = notifier.replay()
    assert summary.total == 2
