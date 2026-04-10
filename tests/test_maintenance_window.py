"""Tests for pipewatch.maintenance_window."""

from datetime import datetime, timedelta

import pytest

from pipewatch.maintenance_window import MaintenanceStore, MaintenanceWindow


@pytest.fixture()
def store() -> MaintenanceStore:
    return MaintenanceStore(db_path=":memory:")


def _window(
    pipeline: str = "pipe_a",
    offset_start: int = -10,
    offset_end: int = 10,
    reason: str = "planned",
) -> MaintenanceWindow:
    now = datetime.utcnow()
    return MaintenanceWindow(
        pipeline_name=pipeline,
        start=now + timedelta(minutes=offset_start),
        end=now + timedelta(minutes=offset_end),
        reason=reason,
    )


# --- MaintenanceWindow.is_active ---

def test_window_active_when_now_inside():
    w = _window(offset_start=-5, offset_end=5)
    assert w.is_active() is True


def test_window_not_active_before_start():
    w = _window(offset_start=5, offset_end=15)
    assert w.is_active() is False


def test_window_not_active_after_end():
    w = _window(offset_start=-20, offset_end=-5)
    assert w.is_active() is False


def test_window_active_at_exact_boundary():
    now = datetime.utcnow()
    w = MaintenanceWindow(pipeline_name="p", start=now, end=now)
    assert w.is_active(at=now) is True


# --- MaintenanceStore.is_in_maintenance ---

def test_not_in_maintenance_when_empty(store):
    assert store.is_in_maintenance("pipe_a") is False


def test_in_maintenance_after_add(store):
    store.add(_window("pipe_a"))
    assert store.is_in_maintenance("pipe_a") is True


def test_not_in_maintenance_for_different_pipeline(store):
    store.add(_window("pipe_a"))
    assert store.is_in_maintenance("pipe_b") is False


def test_not_in_maintenance_for_expired_window(store):
    store.add(_window(offset_start=-20, offset_end=-5))
    assert store.is_in_maintenance("pipe_a") is False


def test_not_in_maintenance_for_future_window(store):
    store.add(_window(offset_start=10, offset_end=30))
    assert store.is_in_maintenance("pipe_a") is False


# --- MaintenanceStore.active_windows ---

def test_active_windows_empty(store):
    assert store.active_windows() == []


def test_active_windows_returns_current(store):
    store.add(_window("pipe_a"))
    store.add(_window("pipe_b"))
    names = {w.pipeline_name for w in store.active_windows()}
    assert names == {"pipe_a", "pipe_b"}


def test_active_windows_excludes_expired(store):
    store.add(_window("pipe_a", offset_start=-30, offset_end=-10))
    store.add(_window("pipe_b"))
    names = {w.pipeline_name for w in store.active_windows()}
    assert names == {"pipe_b"}


# --- MaintenanceStore.remove_expired ---

def test_remove_expired_returns_count(store):
    store.add(_window(offset_start=-30, offset_end=-10))
    store.add(_window(offset_start=-30, offset_end=-10))
    removed = store.remove_expired()
    assert removed == 2


def test_remove_expired_leaves_active(store):
    store.add(_window())  # active
    store.add(_window(offset_start=-30, offset_end=-10))  # expired
    store.remove_expired()
    assert store.is_in_maintenance("pipe_a") is True
