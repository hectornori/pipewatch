"""Tests for pipewatch.suppression."""

import time

import pytest

from pipewatch.suppression import SuppressionStore


@pytest.fixture
def store() -> SuppressionStore:
    return SuppressionStore(db_path=":memory:")


def test_not_suppressed_when_no_record(store: SuppressionStore) -> None:
    assert store.is_suppressed("my_pipeline", cooldown_seconds=300) is False


def test_last_alerted_at_none_before_record(store: SuppressionStore) -> None:
    assert store.last_alerted_at("my_pipeline") is None


def test_record_alert_stores_timestamp(store: SuppressionStore) -> None:
    before = time.time()
    store.record_alert("my_pipeline")
    after = time.time()
    ts = store.last_alerted_at("my_pipeline")
    assert ts is not None
    assert before <= ts <= after


def test_is_suppressed_within_cooldown(store: SuppressionStore) -> None:
    store.record_alert("my_pipeline")
    assert store.is_suppressed("my_pipeline", cooldown_seconds=300) is True


def test_is_not_suppressed_after_cooldown(store: SuppressionStore, monkeypatch) -> None:
    store.record_alert("my_pipeline")
    # Simulate time passing beyond the cooldown window
    future = time.time() + 400
    monkeypatch.setattr("pipewatch.suppression.time.time", lambda: future)
    assert store.is_suppressed("my_pipeline", cooldown_seconds=300) is False


def test_record_alert_overwrites_previous(store: SuppressionStore, monkeypatch) -> None:
    store.record_alert("my_pipeline")
    first_ts = store.last_alerted_at("my_pipeline")
    later = time.time() + 60
    monkeypatch.setattr("pipewatch.suppression.time.time", lambda: later)
    store.record_alert("my_pipeline")
    second_ts = store.last_alerted_at("my_pipeline")
    assert second_ts is not None
    assert second_ts >= first_ts  # type: ignore[operator]


def test_clear_removes_record(store: SuppressionStore) -> None:
    store.record_alert("my_pipeline")
    store.clear("my_pipeline")
    assert store.last_alerted_at("my_pipeline") is None
    assert store.is_suppressed("my_pipeline", cooldown_seconds=300) is False


def test_clear_nonexistent_pipeline_is_noop(store: SuppressionStore) -> None:
    # Should not raise
    store.clear("nonexistent_pipeline")


def test_multiple_pipelines_are_independent(store: SuppressionStore) -> None:
    store.record_alert("pipeline_a")
    assert store.is_suppressed("pipeline_a", cooldown_seconds=300) is True
    assert store.is_suppressed("pipeline_b", cooldown_seconds=300) is False
