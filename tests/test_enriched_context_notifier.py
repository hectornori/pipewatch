"""Tests for EnrichedContextNotifier."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

import pytest

from pipewatch.notifiers.enriched_context_notifier import EnrichedContextNotifier, _enrich
from pipewatch.ownership import OwnershipEntry, OwnershipStore
from pipewatch.on_call import OnCallEntry, OnCallStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool
    error_message: str | None = None


class _FakeInner:
    def __init__(self):
        self.received: List = []

    def send(self, result) -> None:
        self.received.append(result)


_NOW = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
_FUTURE = datetime(2099, 1, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def ownership_store():
    conn = sqlite3.connect(":memory:")
    return OwnershipStore(conn=conn)


@pytest.fixture()
def on_call_store():
    conn = sqlite3.connect(":memory:")
    return OnCallStore(conn=conn)


@pytest.fixture()
def inner():
    return _FakeInner()


@pytest.fixture()
def notifier(inner, ownership_store, on_call_store):
    return EnrichedContextNotifier(
        inner=inner,
        ownership_store=ownership_store,
        on_call_store=on_call_store,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_send_forwards_to_inner(notifier, inner):
    result = _FakeResult(pipeline_name="pipe_a", success=True)
    notifier.send(result)
    assert len(inner.received) == 1


def test_owner_none_when_no_entry(notifier, inner):
    result = _FakeResult(pipeline_name="pipe_a", success=False)
    notifier.send(result)
    assert inner.received[0].owner is None


def test_on_call_none_when_no_entry(notifier, inner):
    result = _FakeResult(pipeline_name="pipe_a", success=False)
    notifier.send(result)
    assert inner.received[0].on_call is None


def test_owner_populated_from_store(notifier, inner, ownership_store):
    entry = OwnershipEntry(pipeline_name="pipe_b", owner="alice", team="data-eng")
    ownership_store.upsert(entry)
    result = _FakeResult(pipeline_name="pipe_b", success=False)
    notifier.send(result)
    assert inner.received[0].owner == "alice"


def test_on_call_populated_from_store(notifier, inner, on_call_store):
    oc = OnCallEntry(
        pipeline_name="pipe_c",
        contact="bob",
        start=_NOW,
        end=_FUTURE,
    )
    on_call_store.upsert(oc)
    result = _FakeResult(pipeline_name="pipe_c", success=False)
    notifier.send(result)
    assert inner.received[0].on_call == "bob"


def test_original_attributes_accessible(notifier, inner):
    result = _FakeResult(pipeline_name="pipe_d", success=True, error_message="oops")
    notifier.send(result)
    enriched = inner.received[0]
    assert enriched.pipeline_name == "pipe_d"
    assert enriched.success is True
    assert enriched.error_message == "oops"
