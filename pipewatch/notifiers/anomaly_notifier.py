"""Notifier that wraps another notifier and fires on anomaly detection."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from pipewatch.anomaly_detector import AnomalyDetector, AnomalyResult
from pipewatch.metric_collector import MetricCollector, PipelineMetric


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


class _AnomalyAlert:
    """Thin wrapper so inner notifiers receive a consistent object."""

    def __init__(self, metric: PipelineMetric, anomaly: AnomalyResult) -> None:
        self.pipeline_name = metric.pipeline_name
        self.success = metric.success
        self.error_message: str = anomaly.reason or "anomalous duration detected"
        self.tags: list = []
        self.severity: str = "warning"
        self._metric = metric
        self._anomaly = anomaly

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AnomalyAlert pipeline={self.pipeline_name!r} "
            f"z_score={self._anomaly.z_score}>"
        )


class AnomalyNotifier:
    """Checks each metric for anomalies and forwards alerts to *inner*."""

    def __init__(
        self,
        inner: Notifier,
        detector: AnomalyDetector,
        collector: MetricCollector,
    ) -> None:
        self._inner = inner
        self._detector = detector
        self._collector = collector

    def handle(self, metric: PipelineMetric) -> None:
        """Evaluate *metric* and send an alert if anomalous."""
        if metric.duration_seconds is None:
            return
        anomaly = self._detector.check(metric.pipeline_name, metric.duration_seconds)
        if anomaly.is_anomalous:
            alert = _AnomalyAlert(metric, anomaly)
            self._inner.send(alert)

    def send(self, result: object) -> None:
        """Satisfy the Notifier protocol; delegates directly to inner."""
        self._inner.send(result)
