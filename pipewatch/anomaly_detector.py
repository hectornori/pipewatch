"""Anomaly detection for pipeline duration and failure patterns."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipewatch.metric_collector import MetricCollector, PipelineMetric


@dataclass
class AnomalyResult:
    pipeline_name: str
    is_anomalous: bool
    reason: Optional[str] = None
    z_score: Optional[float] = None

    def __bool__(self) -> bool:
        return self.is_anomalous


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _stddev(values: List[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


class AnomalyDetector:
    """Detects anomalous pipeline durations using z-score analysis."""

    def __init__(
        self,
        collector: MetricCollector,
        z_threshold: float = 3.0,
        min_samples: int = 5,
        lookback: int = 50,
    ) -> None:
        if z_threshold <= 0:
            raise ValueError("z_threshold must be positive")
        if min_samples < 2:
            raise ValueError("min_samples must be at least 2")
        self.collector = collector
        self.z_threshold = z_threshold
        self.min_samples = min_samples
        self.lookback = lookback

    def check(self, pipeline_name: str, current_duration: float) -> AnomalyResult:
        recent: List[PipelineMetric] = self.collector.get_recent(
            pipeline_name, limit=self.lookback
        )
        durations = [
            m.duration_seconds for m in recent if m.duration_seconds is not None
        ]
        if len(durations) < self.min_samples:
            return AnomalyResult(pipeline_name=pipeline_name, is_anomalous=False)

        mean = _mean(durations)
        std = _stddev(durations, mean)
        if std == 0:
            return AnomalyResult(pipeline_name=pipeline_name, is_anomalous=False)

        z = abs(current_duration - mean) / std
        if z >= self.z_threshold:
            return AnomalyResult(
                pipeline_name=pipeline_name,
                is_anomalous=True,
                reason=(
                    f"duration {current_duration:.2f}s is {z:.1f} stds "
                    f"from mean {mean:.2f}s"
                ),
                z_score=z,
            )
        return AnomalyResult(
            pipeline_name=pipeline_name, is_anomalous=False, z_score=z
        )

    def check_all(self, metrics: List[PipelineMetric]) -> List[AnomalyResult]:
        results = []
        for metric in metrics:
            if metric.duration_seconds is not None:
                results.append(self.check(metric.pipeline_name, metric.duration_seconds))
        return results
