"""Retry logic for pipeline checks."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Defines how retries should be attempted for a pipeline check."""

    max_attempts: int = 3
    delay_seconds: float = 5.0
    backoff_factor: float = 2.0
    exceptions: tuple = field(default_factory=lambda: (Exception,))

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds must be non-negative")
        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be >= 1.0")


def with_retry(
    fn: Callable,
    policy: RetryPolicy,
    *args,
    **kwargs,
):
    """Execute *fn* with the given *policy*, retrying on allowed exceptions.

    Returns the function's return value on success.
    Raises the last exception when all attempts are exhausted.
    """
    last_exc: Optional[Exception] = None
    delay = policy.delay_seconds

    for attempt in range(1, policy.max_attempts + 1):
        try:
            result = fn(*args, **kwargs)
            if attempt > 1:
                logger.info("Succeeded on attempt %d/%d", attempt, policy.max_attempts)
            return result
        except policy.exceptions as exc:  # type: ignore[misc]
            last_exc = exc
            if attempt < policy.max_attempts:
                logger.warning(
                    "Attempt %d/%d failed (%s). Retrying in %.1fs …",
                    attempt,
                    policy.max_attempts,
                    exc,
                    delay,
                )
                time.sleep(delay)
                delay *= policy.backoff_factor
            else:
                logger.error(
                    "All %d attempts failed. Last error: %s",
                    policy.max_attempts,
                    exc,
                )

    raise last_exc  # type: ignore[misc]


def policy_from_dict(data: dict) -> RetryPolicy:
    """Build a :class:`RetryPolicy` from a plain dictionary (e.g. parsed YAML)."""
    return RetryPolicy(
        max_attempts=int(data.get("max_attempts", 3)),
        delay_seconds=float(data.get("delay_seconds", 5.0)),
        backoff_factor=float(data.get("backoff_factor", 2.0)),
    )
