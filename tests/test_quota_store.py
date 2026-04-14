"""Unit tests for QuotaStore."""
import time

import pytest

from pipewatch.notifiers.quota_notifier import QuotaStore


@pytest.fixture
def store() -> QuotaStore:
    return QuotaStore(db_path=":memory:")


def test_count_zero_before_any_record(store: QuotaStore) -> None:
    assert store.count_since("pipe_a", time.time() - 3600) == 0


def test_record_increments_count(store: QuotaStore) -> None:
    now = time.time()
    store.record("pipe_a", ts=now)
    assert store.count_since("pipe_a", now - 10) == 1


def test_old_records_excluded(store: QuotaStore) -> None:
    old = time.time() - 7200
    store.record("pipe_a", ts=old)
    assert store.count_since("pipe_a", time.time() - 3600) == 0


def test_count_isolated_per_pipeline(store: QuotaStore) -> None:
    now = time.time()
    store.record("pipe_a", ts=now)
    store.record("pipe_a", ts=now)
    store.record("pipe_b", ts=now)
    assert store.count_since("pipe_a", now - 10) == 2
    assert store.count_since("pipe_b", now - 10) == 1


def test_not_over_quota_when_under_limit(store: QuotaStore) -> None:
    now = time.time()
    store.record("pipe_a", ts=now)
    assert not store.is_over_quota("pipe_a", max_count=5, window_seconds=3600)


def test_over_quota_at_limit(store: QuotaStore) -> None:
    now = time.time()
    for _ in range(3):
        store.record("pipe_a", ts=now)
    assert store.is_over_quota("pipe_a", max_count=3, window_seconds=3600)


def test_not_over_quota_for_different_pipeline(store: QuotaStore) -> None:
    now = time.time()
    for _ in range(10):
        store.record("pipe_a", ts=now)
    assert not store.is_over_quota("pipe_b", max_count=3, window_seconds=3600)
