"""Configuration helpers for CorrelationNotifier."""
from __future__ import annotations

from dataclasses import dataclass

from pipewatch.notifiers.correlation_notifier import CorrelationNotifier, CorrelationWindow


@dataclass
class CorrelationConfig:
    window_seconds: int = 60

    def __post_init__(self) -> None:
        if self.window_seconds <= 0:
            raise ValueError(
                f"window_seconds must be positive, got {self.window_seconds}"
            )


def correlation_config_from_dict(data: dict) -> CorrelationConfig:
    """Build a CorrelationConfig from a plain dictionary (e.g. parsed YAML)."""
    return CorrelationConfig(
        window_seconds=int(data.get("window_seconds", 60)),
    )


def wrap_with_correlation(
    inner: object,
    config: CorrelationConfig | None = None,
) -> CorrelationNotifier:
    """Wrap *inner* notifier with a CorrelationNotifier using *config*."""
    cfg = config or CorrelationConfig()
    window = CorrelationWindow(window_seconds=cfg.window_seconds)
    return CorrelationNotifier(inner=inner, window=window)  # type: ignore[arg-type]
