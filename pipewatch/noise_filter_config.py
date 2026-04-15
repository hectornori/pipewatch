"""Configuration helpers for NoiseFilterNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pipewatch.notifiers.noise_filter_notifier import NoiseFilterNotifier, Notifier


@dataclass
class NoiseFilterConfig:
    """Validated configuration for the noise-filter notifier wrapper."""

    min_failures: int = 3

    def __post_init__(self) -> None:
        if not isinstance(self.min_failures, int):
            raise TypeError("min_failures must be an integer")
        if self.min_failures < 1:
            raise ValueError("min_failures must be >= 1")


def noise_filter_config_from_dict(raw: dict[str, Any]) -> NoiseFilterConfig:
    """Build a NoiseFilterConfig from a raw mapping (e.g. from YAML)."""
    return NoiseFilterConfig(
        min_failures=int(raw.get("min_failures", 3)),
    )


def wrap_with_noise_filter(inner: Notifier, raw: dict[str, Any]) -> NoiseFilterNotifier:
    """Convenience factory: parse config and wrap *inner* notifier."""
    cfg = noise_filter_config_from_dict(raw)
    return NoiseFilterNotifier(inner=inner, min_failures=cfg.min_failures)
