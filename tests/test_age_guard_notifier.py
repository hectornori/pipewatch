"""Tests for AgeGuardNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from pipewatch.notifiers.age_guard_notifier import AgeGuardNotifier


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe"
    success: bool = True
    checked_at: datetime | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[object] = []

    def send(self, result: object) -> None:
        self.received.append(result)


_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier) -> AgeGuardNotifier:
    return AgeGuardNotifier(
        inner=inner,
        max_age_seconds=60,
        clock=lambda: _NOW,
    )


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult(checked_at=_NOW)


def test_invalid_max_age_zero_raises() -> None:
    with pytest.raises(ValueError, match="max_age_seconds must be > 0"):
        AgeGuardNotifier(inner=_FakeNotifier(), max_age_seconds=0)


def test_invalid_max_age_negative_raises() -> None:
    with pytest.raises(ValueError, match="max_age_seconds must be > 0"):
        AgeGuardNotifier(inner=_FakeNotifier(), max_age_seconds=-5)


def test_send_forwards_fresh_result(
    notifier: AgeGuardNotifier, inner: _FakeNotifier, result: _FakeResult
) -> None:
    notifier.send(result)
    assert inner.received == [result]


def test_send_drops_stale_result(
    notifier: AgeGuardNotifier, inner: _FakeNotifier
) -> None:
    stale = _FakeResult(checked_at=_NOW - timedelta(seconds=61))
    notifier.send(stale)
    assert inner.received == []


def test_send_forwards_result_exactly_at_boundary(
    notifier: AgeGuardNotifier, inner: _FakeNotifier
) -> None:
    # Age == max_age_seconds is NOT older-than, so it should pass.
    boundary = _FakeResult(checked_at=_NOW - timedelta(seconds=60))
    notifier.send(boundary)
    assert inner.received == [boundary]


def test_send_forwards_result_without_checked_at(
    notifier: AgeGuardNotifier, inner: _FakeNotifier
) -> None:
    """Results with no checked_at attribute are forwarded unconditionally."""
    bare = _FakeResult(checked_at=None)
    notifier.send(bare)
    assert inner.received == [bare]


def test_send_handles_naive_datetime(
    notifier: AgeGuardNotifier, inner: _FakeNotifier
) -> None:
    """Naive datetimes are treated as UTC and compared correctly."""
    naive_fresh = _FakeResult(
        checked_at=_NOW.replace(tzinfo=None) - timedelta(seconds=30)
    )
    notifier.send(naive_fresh)
    assert inner.received == [naive_fresh]


def test_default_clock_is_used_when_none_provided(inner: _FakeNotifier) -> None:
    """Constructing without a clock should not raise."""
    n = AgeGuardNotifier(inner=inner, max_age_seconds=3600)
    # A result timestamped right now should pass through.
    fresh = _FakeResult(checked_at=datetime.now(timezone.utc))
    n.send(fresh)
    assert len(inner.received) == 1
