"""Tests for snapshot_notifier_config helpers."""
from __future__ import annotations

import pytest

from pipewatch.snapshot_notifier_config import (
    SnapshotNotifierConfig,
    snapshot_notifier_config_from_dict,
    wrap_with_snapshot,
)
from pipewatch.notifiers.snapshot_notifier import SnapshotNotifier


class _FakeNotifier:
    def send(self, result) -> None:
        pass


def test_default_config_creates_successfully():
    cfg = SnapshotNotifierConfig()
    assert cfg.db_path == ":memory:"


def test_empty_db_path_raises():
    with pytest.raises(ValueError, match="db_path"):
        SnapshotNotifierConfig(db_path="")


def test_from_dict_defaults():
    cfg = snapshot_notifier_config_from_dict({})
    assert cfg.db_path == ":memory:"


def test_from_dict_custom_path():
    cfg = snapshot_notifier_config_from_dict({"db_path": "/tmp/snap.db"})
    assert cfg.db_path == "/tmp/snap.db"


def test_wrap_returns_snapshot_notifier():
    cfg = SnapshotNotifierConfig()
    wrapped = wrap_with_snapshot(_FakeNotifier(), cfg)
    assert isinstance(wrapped, SnapshotNotifier)


def test_wrap_uses_provided_db_path(tmp_path):
    db = str(tmp_path / "snap.db")
    cfg = SnapshotNotifierConfig(db_path=db)
    wrapped = wrap_with_snapshot(_FakeNotifier(), cfg)
    assert wrapped.store.db_path == db
