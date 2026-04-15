"""Build a ScheduleAwareNotifier from config dict."""
from __future__ import annotations

from typing import Any

from pipewatch.schedule_config import schedule_config_from_dict, wrap_with_schedule


def build_schedule_notifier(
    notifier: object,
    config: dict[str, Any],
) -> object:
    """Wrap *notifier* with schedule-awareness using the provided config dict.

    Expected config keys:
        allowed_days: list[str | int]  (e.g. ["Mon","Tue"] or [0, 1])
        start_time: str  HH:MM
        end_time: str    HH:MM

    Returns the wrapped notifier, or the original if no schedule key present.
    """
    if "schedule" not in config:
        return notifier

    schedule_cfg = schedule_config_from_dict(config["schedule"])
    return wrap_with_schedule(notifier, schedule_cfg)


def build_schedule_notifier_from_raw(
    notifier: object,
    allowed_days: list[Any],
    start_time: str,
    end_time: str,
) -> object:
    """Convenience builder accepting raw parameters directly."""
    cfg_dict = {
        "allowed_days": allowed_days,
        "start_time": start_time,
        "end_time": end_time,
    }
    schedule_cfg = schedule_config_from_dict(cfg_dict)
    return wrap_with_schedule(notifier, schedule_cfg)
