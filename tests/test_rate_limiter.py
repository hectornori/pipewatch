"""Tests for pipewatch.rate_limiter."""

from __future__ import annotations

import time

import pytest

from pipewatch.rate_limiter import RateLimiter, limiter_from_config


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter(db_path=":memory:", default_window_seconds=60)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_invalid_window_raises() -> None:
    with pytest.raises(ValueError, match="window_seconds must be positive"):
        RateLimiter(default_window_seconds=0)


def test_negative_window_raises() -> None:
    with pytest.raises(ValueError):
        RateLimiter(default_window_seconds=-10)


# ---------------------------------------------------------------------------
# is_rate_limited
# ---------------------------------------------------------------------------

def test_not_limited_when_no_record(limiter: RateLimiter) -> None:
    assert limiter.is_rate_limited("pipe_a") is False


def test_limited_immediately_after_record(limiter: RateLimiter) -> None:
    limiter.record_sent("pipe_a")
    assert limiter.is_rate_limited("pipe_a") is True


def test_not_limited_after_window_expires(limiter: RateLimiter) -> None:
    limiter.record_sent("pipe_a")
    # Use a very short custom window so the record is already outside it
    assert limiter.is_rate_limited("pipe_a", window_seconds=0) is False


def test_limited_respects_per_call_window(limiter: RateLimiter) -> None:
    limiter.record_sent("pipe_b")
    assert limiter.is_rate_limited("pipe_b", window_seconds=3600) is True


def test_different_pipelines_are_independent(limiter: RateLimiter) -> None:
    limiter.record_sent("pipe_x")
    assert limiter.is_rate_limited("pipe_y") is False


# ---------------------------------------------------------------------------
# count_in_window
# ---------------------------------------------------------------------------

def test_count_zero_before_any_record(limiter: RateLimiter) -> None:
    assert limiter.count_in_window("pipe_a") == 0


def test_count_increments_with_each_record(limiter: RateLimiter) -> None:
    limiter.record_sent("pipe_a")
    limiter.record_sent("pipe_a")
    assert limiter.count_in_window("pipe_a") == 2


def test_count_excludes_expired_records(limiter: RateLimiter) -> None:
    limiter.record_sent("pipe_a")
    # window of 0 seconds — record is already outside it
    assert limiter.count_in_window("pipe_a", window_seconds=0) == 0


# ---------------------------------------------------------------------------
# purge_old_records
# ---------------------------------------------------------------------------

def test_purge_removes_old_records(limiter: RateLimiter) -> None:
    limiter.record_sent("pipe_a")
    deleted = limiter.purge_old_records(window_seconds=0)
    assert deleted == 1
    assert limiter.count_in_window("pipe_a") == 0


def test_purge_keeps_recent_records(limiter: RateLimiter) -> None:
    limiter.record_sent("pipe_a")
    deleted = limiter.purge_old_records(window_seconds=3600)
    assert deleted == 0
    assert limiter.count_in_window("pipe_a") == 1


# ---------------------------------------------------------------------------
# limiter_from_config
# ---------------------------------------------------------------------------

def test_limiter_from_config_defaults() -> None:
    lim = limiter_from_config({})
    assert lim.default_window_seconds == 300
    assert lim.db_path == ":memory:"


def test_limiter_from_config_custom() -> None:
    lim = limiter_from_config({"window_seconds": "120", "db_path": ":memory:"})
    assert lim.default_window_seconds == 120
