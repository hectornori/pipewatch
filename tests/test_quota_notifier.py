"""Unit tests for QuotaNotifier."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.quota_notifier import QuotaNotifier, QuotaStore


@dataclass
class _FakeResult:
    pipeline_name: str = "test_pipe"
    success: bool = True
    error_message: str | None = None


@dataclass
class _FakeNotifier:
    calls: List[_FakeResult] = field(default_factory=list)

    def send(self, result: _FakeResult) -> None:
        self.calls.append(result)


@pytest.fixture
def store() -> QuotaStore:
    return QuotaStore(db_path=":memory:")


@pytest.fixture
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture
def notifier(inner: _FakeNotifier, store: QuotaStore) -> QuotaNotifier:
    return QuotaNotifier(inner=inner, store=store, max_count=3, window_seconds=3600)


def test_send_forwards_when_under_quota(notifier: QuotaNotifier, inner: _FakeNotifier) -> None:
    notifier.send(_FakeResult())
    assert len(inner.calls) == 1


def test_send_blocked_when_quota_exhausted(notifier: QuotaNotifier, inner: _FakeNotifier, store: QuotaStore) -> None:
    now = time.time()
    for _ in range(3):
        store.record("test_pipe", ts=now)
    notifier.send(_FakeResult())
    assert len(inner.calls) == 0


def test_quota_resets_after_window(notifier: QuotaNotifier, inner: _FakeNotifier, store: QuotaStore) -> None:
    old = time.time() - 7200
    for _ in range(3):
        store.record("test_pipe", ts=old)
    notifier.send(_FakeResult())
    assert len(inner.calls) == 1


def test_each_send_records_event(notifier: QuotaNotifier, store: QuotaStore) -> None:
    notifier.send(_FakeResult())
    notifier.send(_FakeResult())
    assert store.count_since("test_pipe", time.time() - 60) == 2


def test_blocked_send_does_not_record(notifier: QuotaNotifier, store: QuotaStore) -> None:
    now = time.time()
    for _ in range(3):
        store.record("test_pipe", ts=now)
    count_before = store.count_since("test_pipe", now - 10)
    notifier.send(_FakeResult())
    assert store.count_since("test_pipe", now - 10) == count_before


def test_different_pipelines_have_independent_quotas(inner: _FakeNotifier, store: QuotaStore) -> None:
    notifier = QuotaNotifier(inner=inner, store=store, max_count=1, window_seconds=3600)
    now = time.time()
    store.record("pipe_a", ts=now)
    notifier.send(_FakeResult(pipeline_name="pipe_b"))
    assert len(inner.calls) == 1
