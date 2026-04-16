"""Tests for HeartbeatNotifier and HeartbeatStore."""
from __future__ import annotations

import time
import pytest

from pipewatch.notifiers.heartbeat_notifier import HeartbeatNotifier, HeartbeatStore
from pipewatch.heartbeat_config import HeartbeatConfig, heartbeat_config_from_dict, wrap_with_heartbeat


class _FakeResult:
    def __init__(self, pipeline_name: str, success: bool = False):
        self.pipeline_name = pipeline_name
        self.success = success


class _FakeNotifier:
    def __init__(self):
        self.received = []

    def send(self, result) -> None:
        self.received.append(result)


@pytest.fixture
def store(tmp_path):
    return HeartbeatStore(db_path=str(tmp_path / "hb.db"))


@pytest.fixture
def inner():
    return _FakeNotifier()


@pytest.fixture
def notifier(store, inner):
    return HeartbeatNotifier(inner=inner, store=store, ttl_seconds=60.0)


@pytest.fixture
def result():
    return _FakeResult(pipeline_name="pipe_a", success=False)


def test_send_forwards_when_no_heartbeat(notifier, inner, result):
    notifier.send(result)
    assert len(inner.received) == 1


def test_send_suppressed_when_heartbeat_fresh(notifier, inner, store, result):
    store.beat("pipe_a")
    notifier.send(result)
    assert len(inner.received) == 0


def test_send_forwards_when_heartbeat_stale(inner, store, result):
    n = HeartbeatNotifier(inner=inner, store=store, ttl_seconds=0.01)
    store.beat("pipe_a")
    time.sleep(0.05)
    n.send(result)
    assert len(inner.received) == 1


def test_is_alive_false_before_beat(store):
    assert store.is_alive("pipe_x", 60.0) is False


def test_is_alive_true_after_beat(store):
    store.beat("pipe_x")
    assert store.is_alive("pipe_x", 60.0) is True


def test_last_beat_at_none_before_beat(store):
    assert store.last_beat_at("pipe_x") is None


def test_last_beat_at_returns_timestamp(store):
    before = time.time()
    store.beat("pipe_x")
    after = time.time()
    ts = store.last_beat_at("pipe_x")
    assert before <= ts <= after


def test_invalid_ttl_raises():
    with pytest.raises(ValueError):
        HeartbeatNotifier(inner=_FakeNotifier(), store=None, ttl_seconds=0)


def test_heartbeat_config_defaults():
    cfg = HeartbeatConfig()
    assert cfg.ttl_seconds == 300.0


def test_heartbeat_config_invalid_ttl_raises():
    with pytest.raises(ValueError):
        HeartbeatConfig(ttl_seconds=-1)


def test_heartbeat_config_from_dict():
    cfg = heartbeat_config_from_dict({"ttl_seconds": 120, "db_path": "hb.db"})
    assert cfg.ttl_seconds == 120.0
    assert cfg.db_path == "hb.db"


def test_wrap_with_heartbeat(tmp_path):
    cfg = HeartbeatConfig(db_path=str(tmp_path / "hb.db"))
    wrapped = wrap_with_heartbeat(_FakeNotifier(), cfg)
    assert isinstance(wrapped, HeartbeatNotifier)
