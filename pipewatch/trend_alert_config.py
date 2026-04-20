"""Configuration helpers for TrendAlertNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pipewatch.notifiers.trend_alert_notifier import TrendAlertNotifier, Notifier
from pipewatch.metric_collector import MetricCollector


@dataclass
class TrendAlertConfig:
    failure_rate_threshold: float = 0.5
    lookback: int = 10
    db_path: str = "pipewatch.db"

    def __post_init__(self) -> None:
        if not 0.0 <= self.failure_rate_threshold <= 1.0:
            raise ValueError(
                "failure_rate_threshold must be between 0.0 and 1.0, "
                f"got {self.failure_rate_threshold}"
            )
        if self.lookback < 1:
            raise ValueError(f"lookback must be >= 1, got {self.lookback}")


def trend_alert_config_from_dict(data: dict[str, Any]) -> TrendAlertConfig:
    return TrendAlertConfig(
        failure_rate_threshold=float(data.get("failure_rate_threshold", 0.5)),
        lookback=int(data.get("lookback", 10)),
        db_path=str(data.get("db_path", "pipewatch.db")),
    )


def wrap_with_trend_alert(
    inner: Notifier,
    config: TrendAlertConfig,
    collector: MetricCollector | None = None,
) -> TrendAlertNotifier:
    if collector is None:
        collector = MetricCollector(db_path=config.db_path)
    return TrendAlertNotifier(
        inner=inner,
        collector=collector,
        failure_rate_threshold=config.failure_rate_threshold,
        lookback=config.lookback,
    )
