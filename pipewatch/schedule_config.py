"""Configuration for schedule-aware notification windows."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import Any

_DAY_NAMES = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3,
    "fri": 4, "sat": 5, "sun": 6,
}


@dataclass
class ScheduleConfig:
    allowed_days: list[int] = field(default_factory=lambda: list(range(7)))
    start_time: time = time(0, 0)
    end_time: time = time(23, 59, 59)

    def __post_init__(self) -> None:
        if not self.allowed_days:
            raise ValueError("allowed_days must not be empty")
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")


def _parse_time(value: str) -> time:
    try:
        h, m = value.split(":")
        return time(int(h), int(m))
    except Exception:
        raise ValueError(f"Invalid time format: {value!r}. Expected HH:MM")


def _parse_days(days: list[str]) -> list[int]:
    result = []
    for d in days:
        key = d.strip().lower()[:3]
        if key not in _DAY_NAMES:
            raise ValueError(f"Unknown day: {d!r}")
        result.append(_DAY_NAMES[key])
    return result


def schedule_config_from_dict(data: dict[str, Any]) -> ScheduleConfig:
    days_raw = data.get("allowed_days", list(_DAY_NAMES.values()))
    if isinstance(days_raw[0], str):
        allowed_days = _parse_days(days_raw)
    else:
        allowed_days = [int(d) for d in days_raw]
    start = _parse_time(data.get("start_time", "00:00"))
    end = _parse_time(data.get("end_time", "23:59"))
    return ScheduleConfig(allowed_days=allowed_days, start_time=start, end_time=end)


def wrap_with_schedule(notifier: object, cfg: ScheduleConfig) -> object:
    from pipewatch.notifiers.schedule_aware_notifier import ScheduleAwareNotifier
    return ScheduleAwareNotifier(
        inner=notifier,
        allowed_days=cfg.allowed_days,
        start_time=cfg.start_time,
        end_time=cfg.end_time,
    )
