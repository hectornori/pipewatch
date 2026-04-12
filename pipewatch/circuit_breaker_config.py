"""Configuration helpers for CircuitBreakerNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class CircuitBreakerConfig:
    """Holds circuit-breaker tuning parameters.

    Attributes:
        failure_threshold: Consecutive failures before the circuit opens.
        recovery_timeout: Seconds to wait before allowing a probe attempt.
        enabled: When False the circuit breaker is bypassed entirely.
    """
    failure_threshold: int = 3
    recovery_timeout: float = 60.0
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError(
                f"failure_threshold must be >= 1, got {self.failure_threshold}"
            )
        if self.recovery_timeout <= 0:
            raise ValueError(
                f"recovery_timeout must be > 0, got {self.recovery_timeout}"
            )


def circuit_breaker_config_from_dict(data: Dict[str, Any]) -> CircuitBreakerConfig:
    """Build a :class:`CircuitBreakerConfig` from a plain dictionary.

    Only keys that correspond to constructor parameters are forwarded;
    unknown keys are silently ignored.

    Example YAML section::

        circuit_breaker:
          failure_threshold: 5
          recovery_timeout: 120
          enabled: true
    """
    return CircuitBreakerConfig(
        failure_threshold=int(data.get("failure_threshold", 3)),
        recovery_timeout=float(data.get("recovery_timeout", 60.0)),
        enabled=bool(data.get("enabled", True)),
    )


def wrap_with_circuit_breaker(
    notifier,
    cfg: CircuitBreakerConfig,
):
    """Optionally wrap *notifier* with a circuit breaker.

    Returns the original notifier unchanged when ``cfg.enabled`` is False.
    """
    if not cfg.enabled:
        return notifier

    from pipewatch.notifiers.circuit_breaker_notifier import CircuitBreakerNotifier  # noqa: PLC0415

    return CircuitBreakerNotifier(
        inner=notifier,
        failure_threshold=cfg.failure_threshold,
        recovery_timeout=cfg.recovery_timeout,
    )
