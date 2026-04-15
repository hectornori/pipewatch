"""Tests for NoiseFilterConfig and related helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.noise_filter_config import (
    NoiseFilterConfig,
    noise_filter_config_from_dict,
    wrap_with_noise_filter,
)
from pipewatch.notifiers.noise_filter_notifier import NoiseFilterNotifier


@dataclass
class _FakeNotifier:
    received: List = field(default_factory=list)

    def send(self, result) -> None:
        self.received.append(result)


def test_default_config_creates_successfully():
    cfg = NoiseFilterConfig()
    assert cfg.min_failures == 3


def test_invalid_min_failures_zero_raises():
    with pytest.raises(ValueError):
        NoiseFilterConfig(min_failures=0)


def test_invalid_min_failures_negative_raises():
    with pytest.raises(ValueError):
        NoiseFilterConfig(min_failures=-1)


def test_non_integer_min_failures_raises():
    with pytest.raises(TypeError):
        NoiseFilterConfig(min_failures="three")  # type: ignore[arg-type]


def test_from_dict_defaults():
    cfg = noise_filter_config_from_dict({})
    assert cfg.min_failures == 3


def test_from_dict_custom_value():
    cfg = noise_filter_config_from_dict({"min_failures": 5})
    assert cfg.min_failures == 5


def test_from_dict_string_coerced_to_int():
    cfg = noise_filter_config_from_dict({"min_failures": "2"})
    assert cfg.min_failures == 2


def test_wrap_with_noise_filter_returns_notifier():
    inner = _FakeNotifier()
    notifier = wrap_with_noise_filter(inner, {"min_failures": 2})
    assert isinstance(notifier, NoiseFilterNotifier)
    assert notifier.min_failures == 2
    assert notifier.inner is inner
