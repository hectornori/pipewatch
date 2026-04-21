"""Tests for ShadowNotifier and ShadowConfig."""
from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import Any

from pipewatch.notifiers.shadow_notifier import ShadowNotifier
from pipewatch.shadow_config import (
    ShadowConfig,
    shadow_config_from_dict,
    wrap_with_shadow,
)


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe"
    success: bool = True
    error_message: str | None = None


@dataclass
class _FakeNotifier:
    received: list[Any] = field(default_factory=list)
    raise_on_send: bool = False

    def send(self, result: Any) -> None:
        if self.raise_on_send:
            raise RuntimeError("boom")
        self.received.append(result)


@pytest.fixture()
def primary() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def shadow_inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(primary: _FakeNotifier, shadow_inner: _FakeNotifier) -> ShadowNotifier:
    return ShadowNotifier(primary=primary, shadow=shadow_inner)


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult()


def test_send_forwards_to_primary(notifier, primary, result):
    notifier.send(result)
    assert result in primary.received


def test_send_mirrors_to_shadow(notifier, shadow_inner, result):
    notifier.send(result)
    assert result in shadow_inner.received


def test_shadow_failure_does_not_propagate(primary, result):
    broken_shadow = _FakeNotifier(raise_on_send=True)
    n = ShadowNotifier(primary=primary, shadow=broken_shadow)
    # Should not raise
    n.send(result)
    assert result in primary.received


def test_shadow_error_count_increments_on_failure(result):
    broken_shadow = _FakeNotifier(raise_on_send=True)
    primary = _FakeNotifier()
    n = ShadowNotifier(primary=primary, shadow=broken_shadow)
    n.send(result)
    n.send(result)
    assert n.shadow_error_count == 2


def test_primary_failure_propagates(shadow_inner, result):
    broken_primary = _FakeNotifier(raise_on_send=True)
    n = ShadowNotifier(primary=broken_primary, shadow=shadow_inner)
    with pytest.raises(RuntimeError):
        n.send(result)


def test_shadow_not_called_when_primary_raises(shadow_inner, result):
    broken_primary = _FakeNotifier(raise_on_send=True)
    n = ShadowNotifier(primary=broken_primary, shadow=shadow_inner)
    try:
        n.send(result)
    except RuntimeError:
        pass
    assert shadow_inner.received == []


# --- ShadowConfig tests ---

def test_default_config_creates_successfully():
    cfg = ShadowConfig()
    assert cfg.enabled is True
    assert cfg.log_divergence is False


def test_from_dict_defaults():
    cfg = shadow_config_from_dict({})
    assert cfg.enabled is True


def test_from_dict_custom_values():
    cfg = shadow_config_from_dict({"enabled": False, "log_divergence": True})
    assert cfg.enabled is False
    assert cfg.log_divergence is True


def test_wrap_with_shadow_returns_shadow_notifier():
    p = _FakeNotifier()
    s = _FakeNotifier()
    wrapped = wrap_with_shadow(p, s)
    assert isinstance(wrapped, ShadowNotifier)


def test_wrap_with_shadow_disabled_returns_primary():
    p = _FakeNotifier()
    s = _FakeNotifier()
    cfg = ShadowConfig(enabled=False)
    wrapped = wrap_with_shadow(p, s, config=cfg)
    assert wrapped is p
