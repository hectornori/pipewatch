"""Tests for AcknowledgeStore, AcknowledgeNotifier, and AcknowledgeConfig."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import List

import pytest

from pipewatch.notifiers.acknowledge_notifier import AcknowledgeStore, AcknowledgeNotifier
from pipewatch.acknowledge_config import (
    AcknowledgeConfig,
    acknowledge_config_from_dict,
    wrap_with_acknowledge,
)


@dataclass
class _FakeResult:
    pipeline: str
    success: bool = True
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[_FakeResult] = []

    def send(self, result: _FakeResult) -> None:
        self.received.append(result)


_future = datetime.now(tz=timezone.utc) + timedelta(hours=1)
_past = datetime.now(tz=timezone.utc) - timedelta(hours=1)


@pytest.fixture()
def store() -> AcknowledgeStore:
    return AcknowledgeStore(db_path=":memory:")


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier, store: AcknowledgeStore) -> AcknowledgeNotifier:
    return AcknowledgeNotifier(inner=inner, store=store)


# --- AcknowledgeStore ---

def test_not_acknowledged_before_any_record(store: AcknowledgeStore) -> None:
    assert store.is_acknowledged("pipe_a") is False


def test_acknowledged_within_window(store: AcknowledgeStore) -> None:
    store.acknowledge("pipe_a", _future)
    assert store.is_acknowledged("pipe_a") is True


def test_not_acknowledged_after_expiry(store: AcknowledgeStore) -> None:
    store.acknowledge("pipe_a", _past)
    assert store.is_acknowledged("pipe_a") is False


def test_unacknowledge_removes_record(store: AcknowledgeStore) -> None:
    store.acknowledge("pipe_a", _future)
    store.unacknowledge("pipe_a")
    assert store.is_acknowledged("pipe_a") is False


def test_reason_stored_and_retrieved(store: AcknowledgeStore) -> None:
    store.acknowledge("pipe_a", _future, reason="planned maintenance")
    assert store.get_reason("pipe_a") == "planned maintenance"


def test_reason_none_when_not_stored(store: AcknowledgeStore) -> None:
    assert store.get_reason("pipe_a") is None


def test_acknowledge_upserts_existing(store: AcknowledgeStore) -> None:
    store.acknowledge("pipe_a", _past, reason="old")
    store.acknowledge("pipe_a", _future, reason="new")
    assert store.is_acknowledged("pipe_a") is True
    assert store.get_reason("pipe_a") == "new"


# --- AcknowledgeNotifier ---

def test_send_forwards_when_not_acknowledged(
    notifier: AcknowledgeNotifier, inner: _FakeNotifier, store: AcknowledgeStore
) -> None:
    result = _FakeResult(pipeline="pipe_a")
    notifier.send(result)
    assert len(inner.received) == 1


def test_send_suppressed_when_acknowledged(
    notifier: AcknowledgeNotifier, inner: _FakeNotifier, store: AcknowledgeStore
) -> None:
    store.acknowledge("pipe_a", _future)
    result = _FakeResult(pipeline="pipe_a")
    notifier.send(result)
    assert len(inner.received) == 0


def test_send_forwards_after_expiry(
    notifier: AcknowledgeNotifier, inner: _FakeNotifier, store: AcknowledgeStore
) -> None:
    store.acknowledge("pipe_a", _past)
    result = _FakeResult(pipeline="pipe_a")
    notifier.send(result)
    assert len(inner.received) == 1


# --- AcknowledgeConfig ---

def test_default_config_creates_successfully() -> None:
    cfg = AcknowledgeConfig()
    assert cfg.db_path == ":memory:"


def test_from_dict_defaults() -> None:
    cfg = acknowledge_config_from_dict({})
    assert cfg.db_path == ":memory:"


def test_from_dict_custom_db_path() -> None:
    cfg = acknowledge_config_from_dict({"db_path": "/tmp/ack.db"})
    assert cfg.db_path == "/tmp/ack.db"


def test_from_dict_invalid_db_path_raises() -> None:
    with pytest.raises(TypeError):
        acknowledge_config_from_dict({"db_path": 42})


def test_wrap_with_acknowledge_returns_notifier() -> None:
    inner = _FakeNotifier()
    wrapped = wrap_with_acknowledge(inner, {})
    assert isinstance(wrapped, AcknowledgeNotifier)
