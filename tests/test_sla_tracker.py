"""Tests for pipewatch.sla_tracker."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pipewatch.sla_tracker import SLABreach, SLATracker


@pytest.fixture
def tracker(tmp_path):
    return SLATracker(db_path=str(tmp_path / "sla.db"))


def _utc(**kwargs) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**kwargs)


# ---------------------------------------------------------------------------
# register / clear
# ---------------------------------------------------------------------------

def test_no_breach_before_register(tracker):
    assert tracker.check_breach("pipe_a") is None


def test_no_breach_when_deadline_in_future(tracker):
    tracker.register("pipe_a", expected_by=_utc(hours=1))
    assert tracker.check_breach("pipe_a") is None


def test_breach_detected_when_overdue(tracker):
    past = _utc(minutes=-30)
    tracker.register("pipe_a", expected_by=past)
    breach = tracker.check_breach("pipe_a")
    assert breach is not None
    assert isinstance(breach, SLABreach)
    assert breach.pipeline_name == "pipe_a"
    assert breach.minutes_overdue >= 29  # allow tiny clock skew


def test_breach_reason_contains_pipeline_name(tracker):
    tracker.register("my_pipeline", expected_by=_utc(minutes=-10))
    breach = tracker.check_breach("my_pipeline")
    assert "my_pipeline" in breach.reason


def test_clear_removes_entry(tracker):
    tracker.register("pipe_a", expected_by=_utc(minutes=-5))
    tracker.clear("pipe_a")
    assert tracker.check_breach("pipe_a") is None


def test_clear_nonexistent_is_safe(tracker):
    tracker.clear("does_not_exist")  # should not raise


def test_register_overwrites_previous_deadline(tracker):
    tracker.register("pipe_a", expected_by=_utc(minutes=-60))
    tracker.register("pipe_a", expected_by=_utc(hours=2))  # push deadline forward
    assert tracker.check_breach("pipe_a") is None


# ---------------------------------------------------------------------------
# check_all_breaches
# ---------------------------------------------------------------------------

def test_check_all_empty_when_none_registered(tracker):
    assert tracker.check_all_breaches() == []


def test_check_all_returns_only_breached(tracker):
    tracker.register("late_pipe", expected_by=_utc(minutes=-15))
    tracker.register("on_time_pipe", expected_by=_utc(hours=1))
    breaches = tracker.check_all_breaches()
    names = [b.pipeline_name for b in breaches]
    assert "late_pipe" in names
    assert "on_time_pipe" not in names


def test_check_all_returns_multiple_breaches(tracker):
    tracker.register("pipe_1", expected_by=_utc(minutes=-5))
    tracker.register("pipe_2", expected_by=_utc(minutes=-10))
    tracker.register("pipe_3", expected_by=_utc(hours=1))
    breaches = tracker.check_all_breaches()
    assert len(breaches) == 2


def test_minutes_overdue_is_positive(tracker):
    tracker.register("pipe_a", expected_by=_utc(minutes=-45))
    breach = tracker.check_breach("pipe_a")
    assert breach.minutes_overdue > 0
