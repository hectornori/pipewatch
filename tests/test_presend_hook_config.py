"""Tests for presend_hook_config helpers."""
from __future__ import annotations

import pytest

from pipewatch.presend_hook_config import (
    PresendHookConfig,
    presend_hook_config_from_dict,
    register_hook,
    wrap_with_presend_hook,
    _REGISTRY,
)
from pipewatch.notifiers.presend_hook_notifier import PresendHookNotifier


class _FakeNotifier:
    def send(self, result) -> None:  # pragma: no cover
        pass


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure hook registry is restored after each test."""
    original = dict(_REGISTRY)
    yield
    _REGISTRY.clear()
    _REGISTRY.update(original)


def test_valid_config_creates_successfully():
    cfg = PresendHookConfig(hook_name="my_hook")
    assert cfg.hook_name == "my_hook"


def test_empty_hook_name_raises():
    with pytest.raises(ValueError, match="hook_name"):
        PresendHookConfig(hook_name="")


def test_from_dict_minimal():
    cfg = presend_hook_config_from_dict({"hook_name": "enrich"})
    assert cfg.hook_name == "enrich"


def test_from_dict_missing_hook_name_raises():
    with pytest.raises(ValueError, match="hook_name"):
        presend_hook_config_from_dict({})


def test_register_hook_stores_callable():
    fn = lambda r: None  # noqa: E731
    register_hook("test_fn", fn)
    assert _REGISTRY["test_fn"] is fn


def test_register_non_callable_raises():
    with pytest.raises(TypeError, match="callable"):
        register_hook("bad", "not_a_function")  # type: ignore[arg-type]


def test_wrap_with_presend_hook_returns_notifier():
    register_hook("noop", lambda r: None)
    cfg = PresendHookConfig(hook_name="noop")
    inner = _FakeNotifier()
    wrapped = wrap_with_presend_hook(inner, cfg)
    assert isinstance(wrapped, PresendHookNotifier)
    assert wrapped.inner is inner


def test_wrap_with_unknown_hook_raises():
    cfg = PresendHookConfig(hook_name="nonexistent")
    with pytest.raises(KeyError, match="nonexistent"):
        wrap_with_presend_hook(_FakeNotifier(), cfg)
