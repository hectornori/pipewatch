"""Stale pipeline detector: flag pipelines that haven't succeeded within a threshold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.checkpoint import CheckpointStore


@dataclass
class StalePipeline:
    name: str
    minutes_since_success: Optional[float]  # None means never succeeded
    threshold_minutes: float

    @property
    def reason(self) -> str:
        if self.minutes_since_success is None:
            return f"{self.name}: no successful run on record"
        return (
            f"{self.name}: last success {self.minutes_since_success:.1f} min ago "
            f"(threshold {self.threshold_minutes:.0f} min)"
        )


@dataclass
class StaleDetector:
    """Check a set of pipelines against their staleness thresholds."""

    store: CheckpointStore
    default_threshold_minutes: float = 60.0

    def check(self, pipeline_name: str, threshold_minutes: Optional[float] = None) -> Optional[StalePipeline]:
        """Return a *StalePipeline* if stale, otherwise None."""
        threshold = threshold_minutes if threshold_minutes is not None else self.default_threshold_minutes
        elapsed = self.store.minutes_since_success(pipeline_name)
        if elapsed is None or elapsed > threshold:
            return StalePipeline(
                name=pipeline_name,
                minutes_since_success=elapsed,
                threshold_minutes=threshold,
            )
        return None

    def check_all(
        self,
        pipelines: List[str],
        thresholds: Optional[dict[str, float]] = None,
    ) -> List[StalePipeline]:
        """Return stale pipelines from *pipelines*, using per-pipeline *thresholds* where provided."""
        thresholds = thresholds or {}
        stale: List[StalePipeline] = []
        for name in pipelines:
            result = self.check(name, thresholds.get(name))
            if result is not None:
                stale.append(result)
        return stale
