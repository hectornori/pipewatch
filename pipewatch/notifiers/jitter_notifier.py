"""Jitter notifier — adds a random delay before forwarding to reduce thundering-herd."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Protocol


class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class JitterNotifier:
    """Wraps an inner notifier and sleeps for a random duration before forwarding.

    Args:
        inner: The downstream notifier to forward to.
        min_seconds: Minimum jitter delay in seconds (default 0).
        max_seconds: Maximum jitter delay in seconds (default 5).
        seed: Optional RNG seed for deterministic testing.
    """

    inner: Notifier
    min_seconds: float = 0.0
    max_seconds: float = 5.0
    seed: int | None = None
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.min_seconds < 0:
            raise ValueError("min_seconds must be >= 0")
        if self.max_seconds < self.min_seconds:
            raise ValueError("max_seconds must be >= min_seconds")
        self._rng = random.Random(self.seed)

    def send(self, result: object) -> None:
        delay = self._rng.uniform(self.min_seconds, self.max_seconds)
        if delay > 0:
            time.sleep(delay)
        self.inner.send(result)
