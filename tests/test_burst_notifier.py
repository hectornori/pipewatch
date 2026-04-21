"""Tests for BurstNotifier and BurstConfig."""
from __future__ import annotations

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from pipewatch.burst_config import BurstConfig, burst_config_from_dict, wrap_with_burst
from pipewatch.notifiers.burst_notifier import BurstNotifier, BurstStore


@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool = True


@pytest.fixture
def store(tmp_path):
    return BurstStore(db_path=str(tmp_path / "burst.db"))


@pytest.fixture
def inner():
    m = MagicMock()
    m.send = MagicMock()
    return m


@pytest.fixture
def notifier(store, inner):
    return BurstNotifier(inner=inner, store=store, max_count=3, window_seconds=60.0)


@pytest.fixture
def result():
    return _FakeResult(pipeline_name="pipe_a")


def test_invalid_max_count_raises(store, inner):
    with pytest.raises(ValueError, match="max_count"):
        BurstNotifier(inner=inner, store=store, max_count=0, window_seconds=60.0)


def test_invalid_window_raises(store, inner):
    with pytest.raises(ValueError, match="window_seconds"):
        BurstNotifier(inner=inner, store=store, max_count=3, window_seconds=0.0)


def test_first_send_forwards(notifier, inner, result):
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_sends_up_to_max_count(notifier, inner, result):
    for _ in range(3):
        notifier.send(result)
    assert inner.send.call_count == 3


def test_send_suppressed_after_max_count(notifier, inner, result):
    for _ in range(3):
        notifier.send(result)
    notifier.send(result)  # 4th – should be suppressed
    assert inner.send.call_count == 3


def test_different_pipelines_tracked_independently(store, inner):
    n = BurstNotifier(inner=inner, store=store, max_count=2, window_seconds=60.0)
    r_a = _FakeResult(pipeline_name="pipe_a")
    r_b = _FakeResult(pipeline_name="pipe_b")
    n.send(r_a)
    n.send(r_a)  # hits limit for pipe_a
    n.send(r_b)  # pipe_b is independent
    n.send(r_b)  # hits limit for pipe_b
    n.send(r_a)  # suppressed
    n.send(r_b)  # suppressed
    assert inner.send.call_count == 4


def test_window_expiry_resets_count(store, inner):
    n = BurstNotifier(inner=inner, store=store, max_count=2, window_seconds=0.05)
    r = _FakeResult(pipeline_name="pipe_x")
    n.send(r)
    n.send(r)  # hits limit
    n.send(r)  # suppressed
    assert inner.send.call_count == 2
    time.sleep(0.1)  # window expires
    n.send(r)  # should go through again
    assert inner.send.call_count == 3


# --- BurstConfig tests ---

def test_burst_config_valid():
    cfg = BurstConfig(max_count=5, window_seconds=30.0)
    assert cfg.max_count == 5
    assert cfg.window_seconds == 30.0
    assert cfg.db_path == "pipewatch_burst.db"


def test_burst_config_invalid_max_count():
    with pytest.raises(ValueError):
        BurstConfig(max_count=0, window_seconds=30.0)


def test_burst_config_invalid_window():
    with pytest.raises(ValueError):
        BurstConfig(max_count=5, window_seconds=-1.0)


def test_burst_config_from_dict():
    cfg = burst_config_from_dict({"max_count": "10", "window_seconds": "120"})
    assert cfg.max_count == 10
    assert cfg.window_seconds == 120.0


def test_burst_config_from_dict_missing_max_count():
    with pytest.raises(KeyError):
        burst_config_from_dict({"window_seconds": 60})


def test_burst_config_from_dict_missing_window():
    with pytest.raises(KeyError):
        burst_config_from_dict({"max_count": 5})


def test_wrap_with_burst_returns_notifier(tmp_path, inner):
    cfg = BurstConfig(max_count=3, window_seconds=60.0, db_path=str(tmp_path / "b.db"))
    wrapped = wrap_with_burst(inner, cfg)
    assert isinstance(wrapped, BurstNotifier)
    assert wrapped.max_count == 3
