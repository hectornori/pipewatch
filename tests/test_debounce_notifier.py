"""Tests for DebounceNotifier and DebounceConfig."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.debounce_notifier import DebounceNotifier, DebounceStore
from pipewatch.debounce_config import DebounceConfig, debounce_config_from_dict, wrap_with_debounce


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe_a"
    success: bool = True
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self):
        self.calls: List[_FakeResult] = []

    def send(self, result) -> None:
        self.calls.append(result)


@pytest.fixture()
def store():
    return DebounceStore(db_path=":memory:")


@pytest.fixture()
def inner():
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner, store):
    return DebounceNotifier(inner=inner, store=store, window_seconds=30.0)


@pytest.fixture()
def result():
    return _FakeResult(pipeline_name="pipe_a")


def test_send_forwards_first_alert(notifier, inner, result):
    notifier.send(result)
    assert len(inner.calls) == 1


def test_send_debounced_within_window(notifier, inner, result):
    notifier.send(result)
    notifier.send(result)
    assert len(inner.calls) == 1


def test_send_forwards_after_window_expires(inner, store, result):
    n = DebounceNotifier(inner=inner, store=store, window_seconds=0.05)
    n.send(result)
    time.sleep(0.1)
    n.send(result)
    assert len(inner.calls) == 2


def test_different_pipelines_not_debounced_together(notifier, inner, store):
    r1 = _FakeResult(pipeline_name="pipe_a")
    r2 = _FakeResult(pipeline_name="pipe_b")
    notifier.send(r1)
    notifier.send(r2)
    assert len(inner.calls) == 2


def test_store_last_sent_at_none_before_record(store):
    assert store.last_sent_at("pipe_x") is None


def test_store_not_debounced_before_record(store):
    assert store.is_debounced("pipe_x", 60.0) is False


def test_store_debounced_immediately_after_record(store):
    store.record("pipe_x")
    assert store.is_debounced("pipe_x", 60.0) is True


def test_invalid_window_raises():
    with pytest.raises(ValueError):
        DebounceNotifier(inner=_FakeNotifier(), store=DebounceStore(), window_seconds=0)


def test_debounce_config_defaults():
    cfg = DebounceConfig()
    assert cfg.window_seconds == 60.0
    assert cfg.db_path == ":memory:"


def test_debounce_config_invalid_window_raises():
    with pytest.raises(ValueError):
        DebounceConfig(window_seconds=-1)


def test_debounce_config_from_dict():
    cfg = debounce_config_from_dict({"window_seconds": 120.0, "db_path": "/tmp/d.db"})
    assert cfg.window_seconds == 120.0
    assert cfg.db_path == "/tmp/d.db"


def test_wrap_with_debounce_returns_notifier():
    cfg = DebounceConfig(window_seconds=10.0)
    n = wrap_with_debounce(_FakeNotifier(), cfg)
    assert isinstance(n, DebounceNotifier)
    assert n.window_seconds == 10.0
