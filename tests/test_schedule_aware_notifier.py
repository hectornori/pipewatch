"""Tests for ScheduleAwareNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any

import pytest

from pipewatch.notifiers.schedule_aware_notifier import ScheduleAwareNotifier


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe"
    success: bool = True
    error_message: str | None = None


@dataclass
class _FakeNotifier:
    calls: list[Any] = field(default_factory=list)

    def send(self, result: object) -> None:
        self.calls.append(result)


@pytest.fixture
def result() -> _FakeResult:
    return _FakeResult()


@pytest.fixture
def inner() -> _FakeNotifier:
    return _FakeNotifier()


def _clock(dt: datetime):
    return lambda: dt


def test_send_forwards_during_allowed_window(inner, result):
    # Monday 10:00
    dt = datetime(2024, 1, 1, 10, 0)  # Monday
    notifier = ScheduleAwareNotifier(
        inner=inner,
        allowed_days=[0],
        start_time=time(9, 0),
        end_time=time(17, 0),
        _clock=_clock(dt),
    )
    notifier.send(result)
    assert len(inner.calls) == 1


def test_send_suppressed_outside_time_window(inner, result):
    dt = datetime(2024, 1, 1, 8, 0)  # Monday, before 09:00
    notifier = ScheduleAwareNotifier(
        inner=inner,
        allowed_days=[0],
        start_time=time(9, 0),
        end_time=time(17, 0),
        _clock=_clock(dt),
    )
    notifier.send(result)
    assert len(inner.calls) == 0


def test_send_suppressed_on_disallowed_day(inner, result):
    dt = datetime(2024, 1, 6, 12, 0)  # Saturday = weekday 5
    notifier = ScheduleAwareNotifier(
        inner=inner,
        allowed_days=[0, 1, 2, 3, 4],  # weekdays only
        start_time=time(0, 0),
        end_time=time(23, 59, 59),
        _clock=_clock(dt),
    )
    notifier.send(result)
    assert len(inner.calls) == 0


def test_send_at_exact_start_time_is_allowed(inner, result):
    dt = datetime(2024, 1, 1, 9, 0)  # Exactly 09:00
    notifier = ScheduleAwareNotifier(
        inner=inner,
        allowed_days=[0],
        start_time=time(9, 0),
        end_time=time(17, 0),
        _clock=_clock(dt),
    )
    notifier.send(result)
    assert len(inner.calls) == 1


def test_send_at_exact_end_time_is_allowed(inner, result):
    dt = datetime(2024, 1, 1, 17, 0)
    notifier = ScheduleAwareNotifier(
        inner=inner,
        allowed_days=[0],
        start_time=time(9, 0),
        end_time=time(17, 0),
        _clock=_clock(dt),
    )
    notifier.send(result)
    assert len(inner.calls) == 1


def test_multiple_sends_only_forwarded_in_window(inner, result):
    in_window = datetime(2024, 1, 1, 12, 0)
    out_window = datetime(2024, 1, 1, 20, 0)
    times = [in_window, out_window, in_window]
    idx = [0]

    def rotating_clock():
        t = times[idx[0] % len(times)]
        idx[0] += 1
        return t

    notifier = ScheduleAwareNotifier(
        inner=inner,
        allowed_days=[0],
        start_time=time(9, 0),
        end_time=time(17, 0),
        _clock=rotating_clock,
    )
    for _ in times:
        notifier.send(result)
    assert len(inner.calls) == 2
