"""Tests for schedule_config module."""
from __future__ import annotations

from datetime import time

import pytest

from pipewatch.schedule_config import (
    ScheduleConfig,
    _parse_days,
    _parse_time,
    schedule_config_from_dict,
    wrap_with_schedule,
)


def test_default_config_is_always_active():
    cfg = ScheduleConfig()
    assert cfg.allowed_days == list(range(7))
    assert cfg.start_time == time(0, 0)
    assert cfg.end_time == time(23, 59, 59)


def test_empty_allowed_days_raises():
    with pytest.raises(ValueError, match="allowed_days"):
        ScheduleConfig(allowed_days=[])


def test_start_after_end_raises():
    with pytest.raises(ValueError, match="start_time"):
        ScheduleConfig(start_time=time(18, 0), end_time=time(9, 0))


def test_start_equal_end_raises():
    with pytest.raises(ValueError, match="start_time"):
        ScheduleConfig(start_time=time(12, 0), end_time=time(12, 0))


def test_parse_time_valid():
    assert _parse_time("09:30") == time(9, 30)


def test_parse_time_with_seconds():
    assert _parse_time("23:59:59") == time(23, 59, 59)


def test_parse_time_invalid_raises():
    with pytest.raises(ValueError, match="Invalid time format"):
        _parse_time("not-a-time")


def test_parse_days_valid():
    assert _parse_days(["Mon", "Wed", "Fri"]) == [0, 2, 4]


def test_parse_days_all_days():
    assert _parse_days(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]) == list(range(7))


def test_parse_days_unknown_raises():
    with pytest.raises(ValueError, match="Unknown day"):
        _parse_days(["Funday"])


def test_from_dict_with_string_days():
    cfg = schedule_config_from_dict({
        "allowed_days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "start_time": "09:00",
        "end_time": "17:00",
    })
    assert cfg.allowed_days == [0, 1, 2, 3, 4]
    assert cfg.start_time == time(9, 0)
    assert cfg.end_time == time(17, 0)


def test_from_dict_with_int_days():
    cfg = schedule_config_from_dict({
        "allowed_days": [0, 1, 2],
        "start_time": "08:00",
        "end_time": "20:00",
    })
    assert cfg.allowed_days == [0, 1, 2]


def test_from_dict_empty_returns_default_config():
    """An empty dict should produce a default (always-active) ScheduleConfig."""
    cfg = schedule_config_from_dict({})
    assert cfg.allowed_days == list(range(7))
    assert cfg.start_time == time(0, 0)
    assert cfg.end_time == time(23, 59, 59)


def test_wrap_with_schedule_returns_schedule_aware_notifier():
    from pipewatch.notifiers.schedule_aware_notifier import ScheduleAwareNotifier
    from dataclasses import dataclass

    @dataclass
    class _Fake:
        def send(self, r): pass

    cfg = ScheduleConfig(allowed_days=[0], start_time=time(9, 0), end_time=time(17, 0))
    wrapped = wrap_with_schedule(_Fake(), cfg)
    assert isinstance(wrapped, ScheduleAwareNotifier)
    assert wrapped.allowed_days == [0]
