"""Tests for pipewatch.mute_manager."""

from datetime import datetime, timedelta, timezone

import pytest

from pipewatch.mute_manager import MuteManager


@pytest.fixture()
def manager(tmp_path):
    return MuteManager(db_path=str(tmp_path / "mutes.db"))


def _future(minutes: int = 60) -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(minutes=minutes)


def _past(minutes: int = 60) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(minutes=minutes)


# ---------------------------------------------------------------------------
# is_muted
# ---------------------------------------------------------------------------

def test_not_muted_when_no_record(manager):
    assert manager.is_muted("pipeline_a") is False


def test_muted_after_mute_call(manager):
    manager.mute("pipeline_a", _future())
    assert manager.is_muted("pipeline_a") is True


def test_not_muted_after_expiry(manager):
    manager.mute("pipeline_a", _past())
    assert manager.is_muted("pipeline_a") is False


def test_mute_does_not_affect_other_pipelines(manager):
    manager.mute("pipeline_a", _future())
    assert manager.is_muted("pipeline_b") is False


# ---------------------------------------------------------------------------
# unmute
# ---------------------------------------------------------------------------

def test_unmute_clears_active_mute(manager):
    manager.mute("pipeline_a", _future())
    manager.unmute("pipeline_a")
    assert manager.is_muted("pipeline_a") is False


def test_unmute_nonexistent_pipeline_is_noop(manager):
    manager.unmute("ghost_pipeline")  # should not raise


# ---------------------------------------------------------------------------
# muted_until
# ---------------------------------------------------------------------------

def test_muted_until_none_when_not_muted(manager):
    assert manager.muted_until("pipeline_a") is None


def test_muted_until_returns_expiry(manager):
    expiry = _future(30)
    manager.mute("pipeline_a", expiry)
    result = manager.muted_until("pipeline_a")
    assert result is not None
    # Allow a small tolerance due to isoformat round-trip
    assert abs((result - expiry).total_seconds()) < 1


def test_muted_until_none_after_expiry(manager):
    manager.mute("pipeline_a", _past())
    assert manager.muted_until("pipeline_a") is None


# ---------------------------------------------------------------------------
# active_mutes
# ---------------------------------------------------------------------------

def test_active_mutes_empty_initially(manager):
    assert manager.active_mutes() == []


def test_active_mutes_lists_current_mutes(manager):
    manager.mute("pipeline_a", _future(), reason="maintenance")
    manager.mute("pipeline_b", _future())
    names = {r["pipeline_name"] for r in manager.active_mutes()}
    assert names == {"pipeline_a", "pipeline_b"}


def test_active_mutes_excludes_expired(manager):
    manager.mute("pipeline_a", _past())
    manager.mute("pipeline_b", _future())
    names = {r["pipeline_name"] for r in manager.active_mutes()}
    assert names == {"pipeline_b"}


def test_active_mutes_reason_stored(manager):
    manager.mute("pipeline_a", _future(), reason="planned downtime")
    record = manager.active_mutes()[0]
    assert record["reason"] == "planned downtime"
