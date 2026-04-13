"""Configuration helpers for the anomaly detector."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AnomalyConfig:
    z_threshold: float = 3.0
    min_samples: int = 5
    lookback: int = 50
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.z_threshold <= 0:
            raise ValueError("z_threshold must be positive")
        if self.min_samples < 2:
            raise ValueError("min_samples must be at least 2")
        if self.lookback < self.min_samples:
            raise ValueError("lookback must be >= min_samples")


def anomaly_config_from_dict(data: Dict[str, Any]) -> AnomalyConfig:
    """Build an :class:`AnomalyConfig` from a plain mapping (e.g. YAML)."""
    return AnomalyConfig(
        z_threshold=float(data.get("z_threshold", 3.0)),
        min_samples=int(data.get("min_samples", 5)),
        lookback=int(data.get("lookback", 50)),
        enabled=bool(data.get("enabled", True)),
    )
