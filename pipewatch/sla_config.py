"""SLA configuration helpers — parse SLA windows from pipeline config."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


@dataclass
class SLAWindow:
    """Describes when a pipeline must complete by, relative to *now*."""

    pipeline_name: str
    # Maximum allowed minutes from the start of the check run
    max_duration_minutes: int

    def deadline_from(self, start: Optional[datetime] = None) -> datetime:
        """Return the absolute deadline given a start time."""
        if start is None:
            start = datetime.now(timezone.utc)
        return start + timedelta(minutes=self.max_duration_minutes)

    def is_breached(self, start: datetime, now: Optional[datetime] = None) -> bool:
        """Return True if the SLA deadline has passed relative to *now*.

        Args:
            start: The datetime when the pipeline run began.
            now:   The current time to check against; defaults to UTC now.
        """
        if now is None:
            now = datetime.now(timezone.utc)
        return now > self.deadline_from(start)


def sla_window_from_dict(pipeline_name: str, data: Dict[str, Any]) -> Optional[SLAWindow]:
    """Parse an SLAWindow from a pipeline config dict, or return None."""
    sla_section = data.get("sla")
    if not sla_section:
        return None
    max_minutes = sla_section.get("max_duration_minutes")
    if max_minutes is None:
        return None
    if not isinstance(max_minutes, int) or max_minutes <= 0:
        raise ValueError(
            f"Pipeline '{pipeline_name}': sla.max_duration_minutes must be a "
            f"positive integer, got {max_minutes!r}"
        )
    return SLAWindow(
        pipeline_name=pipeline_name,
        max_duration_minutes=max_minutes,
    )


def sla_windows_from_config(pipelines: List[Dict[str, Any]]) -> List[SLAWindow]:
    """Extract all SLA windows from a list of pipeline config dicts."""
    windows: List[SLAWindow] = []
    for pipeline in pipelines:
        name = pipeline.get("name", "")
        window = sla_window_from_dict(name, pipeline)
        if window is not None:
            windows.append(window)
    return windows
