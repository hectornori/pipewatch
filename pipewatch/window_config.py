"""Configuration helpers for WindowNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any, Dict, Optional


@dataclass
class WindowConfig:
    """Parsed time-window configuration."""

    start: time
    end: time
    tz: Optional[str] = None

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError(
                f"window.start ({self.start}) must be before window.end ({self.end})"
            )

    @staticmethod
    def _parse_time(value: str) -> time:
        """Parse HH:MM string into a :class:`datetime.time`."""
        try:
            h, m = value.split(":")
            return time(int(h), int(m))
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid time string '{value}' – expected HH:MM") from exc


def window_config_from_dict(data: Dict[str, Any]) -> WindowConfig:
    """Build a :class:`WindowConfig` from a raw config dictionary."""
    if "start" not in data:
        raise KeyError("window config requires 'start'")
    if "end" not in data:
        raise KeyError("window config requires 'end'")

    start = WindowConfig._parse_time(data["start"])
    end = WindowConfig._parse_time(data["end"])
    tz = data.get("tz")
    return WindowConfig(start=start, end=end, tz=tz)


def wrap_with_window(notifier, data: Dict[str, Any]):
    """Convenience: wrap *notifier* in a WindowNotifier using *data* config."""
    from pipewatch.notifiers.window_notifier import WindowNotifier  # local import

    cfg = window_config_from_dict(data)
    return WindowNotifier(inner=notifier, start=cfg.start, end=cfg.end, tz=cfg.tz)
