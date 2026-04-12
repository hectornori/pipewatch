"""Tests for circuit_breaker_config helpers."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.circuit_breaker_config import (
    CircuitBreakerConfig,
    circuit_breaker_config_from_dict,
    wrap_with_circuit_breaker,
)
from pipewatch.notifiers.circuit_breaker_notifier import CircuitBreakerNotifier


# ------------------------------------------------------------------ #
# CircuitBreakerConfig                                                #
# ------------------------------------------------------------------ #

def test_default_config():
    cfg = CircuitBreakerConfig()
    assert cfg.failure_threshold == 3
    assert cfg.recovery_timeout == 60.0
    assert cfg.enabled is True


def test_invalid_failure_threshold_raises():
    with pytest.raises(ValueError, match="failure_threshold"):
        CircuitBreakerConfig(failure_threshold=0)


def test_invalid_recovery_timeout_raises():
    with pytest.raises(ValueError, match="recovery_timeout"):
        CircuitBreakerConfig(recovery_timeout=0.0)


def test_negative_recovery_timeout_raises():
    with pytest.raises(ValueError, match="recovery_timeout"):
        CircuitBreakerConfig(recovery_timeout=-5.0)


# ------------------------------------------------------------------ #
# circuit_breaker_config_from_dict                                    #
# ------------------------------------------------------------------ #

def test_from_dict_defaults():
    cfg = circuit_breaker_config_from_dict({})
    assert cfg.failure_threshold == 3
    assert cfg.recovery_timeout == 60.0
    assert cfg.enabled is True


def test_from_dict_custom_values():
    cfg = circuit_breaker_config_from_dict(
        {"failure_threshold": 5, "recovery_timeout": 120, "enabled": False}
    )
    assert cfg.failure_threshold == 5
    assert cfg.recovery_timeout == 120.0
    assert cfg.enabled is False


def test_from_dict_ignores_unknown_keys():
    cfg = circuit_breaker_config_from_dict({"unknown_key": "value"})
    assert cfg.failure_threshold == 3  # default unchanged


# ------------------------------------------------------------------ #
# wrap_with_circuit_breaker                                           #
# ------------------------------------------------------------------ #

def test_wrap_returns_circuit_breaker_when_enabled():
    inner = MagicMock()
    cfg = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=30.0)
    wrapped = wrap_with_circuit_breaker(inner, cfg)
    assert isinstance(wrapped, CircuitBreakerNotifier)
    assert wrapped.failure_threshold == 2
    assert wrapped.recovery_timeout == 30.0


def test_wrap_returns_original_when_disabled():
    inner = MagicMock()
    cfg = CircuitBreakerConfig(enabled=False)
    wrapped = wrap_with_circuit_breaker(inner, cfg)
    assert wrapped is inner
