"""Tests for pipewatch.deduplication."""

import time

import pytest

from pipewatch.deduplication import DeduplicationStore


@pytest.fixture
def store() -> DeduplicationStore:
    return DeduplicationStore(db_path=":memory:", window_seconds=60)


# ---------------------------------------------------------------------------
# make_key
# ---------------------------------------------------------------------------

def test_make_key_is_deterministic():
    k1 = DeduplicationStore.make_key("pipeline_a", "some error")
    k2 = DeduplicationStore.make_key("pipeline_a", "some error")
    assert k1 == k2


def test_make_key_differs_by_pipeline():
    k1 = DeduplicationStore.make_key("pipeline_a", "err")
    k2 = DeduplicationStore.make_key("pipeline_b", "err")
    assert k1 != k2


def test_make_key_differs_by_error():
    k1 = DeduplicationStore.make_key("pipeline_a", "err1")
    k2 = DeduplicationStore.make_key("pipeline_a", "err2")
    assert k1 != k2


def test_make_key_none_error_stable():
    k = DeduplicationStore.make_key("pipeline_a", None)
    assert isinstance(k, str) and len(k) == 64


# ---------------------------------------------------------------------------
# is_duplicate / record
# ---------------------------------------------------------------------------

def test_not_duplicate_when_no_record(store):
    key = DeduplicationStore.make_key("pipe", "oops")
    assert store.is_duplicate(key) is False


def test_is_duplicate_after_record(store):
    key = DeduplicationStore.make_key("pipe", "oops")
    store.record(key)
    assert store.is_duplicate(key) is True


def test_not_duplicate_after_window_expires():
    s = DeduplicationStore(db_path=":memory:", window_seconds=1)
    key = DeduplicationStore.make_key("pipe", "oops")
    s.record(key)
    assert s.is_duplicate(key) is True
    time.sleep(1.1)
    assert s.is_duplicate(key) is False


def test_different_pipelines_independent(store):
    k1 = DeduplicationStore.make_key("pipe_a", "err")
    k2 = DeduplicationStore.make_key("pipe_b", "err")
    store.record(k1)
    assert store.is_duplicate(k1) is True
    assert store.is_duplicate(k2) is False


# ---------------------------------------------------------------------------
# purge_expired
# ---------------------------------------------------------------------------

def test_purge_expired_removes_old_entries():
    s = DeduplicationStore(db_path=":memory:", window_seconds=1)
    key = DeduplicationStore.make_key("pipe", "err")
    s.record(key)
    time.sleep(1.1)
    deleted = s.purge_expired()
    assert deleted == 1
    assert s.is_duplicate(key) is False


def test_purge_expired_keeps_recent_entries(store):
    key = DeduplicationStore.make_key("pipe", "err")
    store.record(key)
    deleted = store.purge_expired()
    assert deleted == 0
    assert store.is_duplicate(key) is True


def test_purge_returns_zero_when_empty(store):
    assert store.purge_expired() == 0
