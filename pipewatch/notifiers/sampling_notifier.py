"""Sampling notifier — forwards only a percentage of alerts to reduce noise."""

from __future__ import annotations

import random
import logging
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class SamplingNotifier:
    """Wraps an inner notifier and forwards alerts at a configurable sample rate.

    Args:
        inner: The downstream notifier to forward sampled alerts to.
        sample_rate: Probability (0.0–1.0) that any given alert is forwarded.
        seed: Optional RNG seed for deterministic behaviour in tests.
    """

    inner: Notifier
    sample_rate: float = 1.0
    seed: int | None = None
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not (0.0 <= self.sample_rate <= 1.0):
            raise ValueError(
                f"sample_rate must be between 0.0 and 1.0, got {self.sample_rate}"
            )
        self._rng = random.Random(self.seed)

    def send(self, result: object) -> None:
        """Probabilistically forward *result* to the inner notifier."""
        roll = self._rng.random()
        if roll < self.sample_rate:
            logger.debug(
                "SamplingNotifier forwarding alert (roll=%.4f, rate=%.4f)",
                roll,
                self.sample_rate,
            )
            self.inner.send(result)
        else:
            pipeline = getattr(result, "pipeline_name", "<unknown>")
            logger.debug(
                "SamplingNotifier dropped alert for '%s' (roll=%.4f, rate=%.4f)",
                pipeline,
                roll,
                self.sample_rate,
            )
