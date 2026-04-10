"""Tests for pipewatch.incident_tracker."""

import time
import pytest

from pipewatch.incident_tracker import IncidentTracker, Incident


@pytest.fixture
def tracker(tmp_path):
    return IncidentTracker(db_path=str(tmp_path / "incidents.db"))


def test_no_open_incident_initially(tracker):
    assert tracker.get_open("pipeline_a") is None


def test_has_open_false_initially(tracker):
    assert tracker.has_open("pipeline_a") is False


def test_open_creates_incident(tracker):
    incident = tracker.open_or_update("pipeline_a", "timeout")
    assert isinstance(incident, Incident)
    assert incident.pipeline_name == "pipeline_a"
    assert incident.error_message == "timeout"
    assert not incident.resolved


def test_open_incident_is_retrievable(tracker):
    tracker.open_or_update("pipeline_a", "timeout")
    result = tracker.get_open("pipeline_a")
    assert result is not None
    assert result.pipeline_name == "pipeline_a"


def test_has_open_true_after_open(tracker):
    tracker.open_or_update("pipeline_a", None)
    assert tracker.has_open("pipeline_a") is True


def test_second_open_updates_last_seen(tracker):
    tracker.open_or_update("pipeline_a", "err1")
    time.sleep(0.01)
    tracker.open_or_update("pipeline_a", "err2")
    incident = tracker.get_open("pipeline_a")
    assert incident is not None
    assert incident.error_message == "err2"
    assert incident.last_seen_at >= incident.opened_at


def test_second_open_does_not_create_duplicate(tracker):
    tracker.open_or_update("pipeline_a", "err1")
    tracker.open_or_update("pipeline_a", "err2")
    rows = tracker._conn.execute(
        "SELECT COUNT(*) FROM incidents WHERE pipeline_name = 'pipeline_a' AND resolved = 0"
    ).fetchone()
    assert rows[0] == 1


def test_resolve_returns_true_when_open(tracker):
    tracker.open_or_update("pipeline_a", "err")
    assert tracker.resolve("pipeline_a") is True


def test_resolve_closes_incident(tracker):
    tracker.open_or_update("pipeline_a", "err")
    tracker.resolve("pipeline_a")
    assert tracker.get_open("pipeline_a") is None


def test_resolve_returns_false_when_no_open(tracker):
    assert tracker.resolve("pipeline_a") is False


def test_resolve_allows_new_incident(tracker):
    tracker.open_or_update("pipeline_a", "err1")
    tracker.resolve("pipeline_a")
    tracker.open_or_update("pipeline_a", "err2")
    assert tracker.has_open("pipeline_a") is True


def test_incidents_are_isolated_per_pipeline(tracker):
    tracker.open_or_update("pipeline_a", "err")
    assert tracker.has_open("pipeline_b") is False


def test_open_with_none_error(tracker):
    incident = tracker.open_or_update("pipeline_a", None)
    assert incident.error_message is None
    stored = tracker.get_open("pipeline_a")
    assert stored.error_message is None
