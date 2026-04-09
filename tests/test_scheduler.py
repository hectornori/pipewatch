"""Tests for pipewatch.scheduler."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.scheduler import Scheduler, ScheduledJob


# ---------------------------------------------------------------------------
# ScheduledJob
# ---------------------------------------------------------------------------


def test_job_is_due_on_first_run():
    job = ScheduledJob(name="test", interval_seconds=60, callback=MagicMock())
    assert job.is_due(time.monotonic()) is True


def test_job_not_due_immediately_after_run():
    cb = MagicMock()
    job = ScheduledJob(name="test", interval_seconds=60, callback=cb)
    job.run()
    assert job.is_due(time.monotonic()) is False


def test_job_due_after_interval_elapsed():
    cb = MagicMock()
    job = ScheduledJob(name="test", interval_seconds=1, callback=cb)
    job.run()
    # Simulate time passing beyond the interval
    job._last_run = time.monotonic() - 2
    assert job.is_due(time.monotonic()) is True


def test_job_run_calls_callback():
    cb = MagicMock()
    job = ScheduledJob(name="test", interval_seconds=10, callback=cb)
    job.run()
    cb.assert_called_once()


def test_job_run_records_last_run_on_exception():
    def boom():
        raise RuntimeError("fail")

    job = ScheduledJob(name="test", interval_seconds=10, callback=boom)
    job.run()  # should not raise
    assert job._last_run is not None


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


def test_register_adds_job():
    scheduler = Scheduler()
    scheduler.register("job1", 30, MagicMock())
    assert len(scheduler._jobs) == 1
    assert scheduler._jobs[0].name == "job1"


def test_register_invalid_interval_raises():
    scheduler = Scheduler()
    with pytest.raises(ValueError, match="positive integer"):
        scheduler.register("bad", 0, MagicMock())


def test_tick_runs_due_jobs():
    cb = MagicMock()
    scheduler = Scheduler()
    scheduler.register("immediate", 1, cb)
    scheduler.tick()
    cb.assert_called_once()


def test_tick_skips_non_due_jobs():
    cb = MagicMock()
    scheduler = Scheduler()
    scheduler.register("slow", 9999, cb)
    # First tick will run it (is_due returns True for first run)
    scheduler.tick()
    cb.reset_mock()
    # Second tick should NOT run it
    scheduler.tick()
    cb.assert_not_called()


def test_tick_runs_multiple_due_jobs():
    cb1, cb2 = MagicMock(), MagicMock()
    scheduler = Scheduler()
    scheduler.register("a", 1, cb1)
    scheduler.register("b", 1, cb2)
    scheduler.tick()
    cb1.assert_called_once()
    cb2.assert_called_once()
