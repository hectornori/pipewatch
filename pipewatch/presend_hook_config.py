"""Configuration helpers for PresendHookNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from pipewatch.notifiers.presend_hook_notifier import PresendHookNotifier


@dataclass
class PresendHookConfig:
    """Holds configuration for a presend hook wrapper."""

    hook_name: str

    def __post_init__(self) -> None:
        if not self.hook_name or not isinstance(self.hook_name, str):
            raise ValueError("hook_name must be a non-empty string")


# Registry of named hook functions.
_REGISTRY: dict[str, Callable[[object], Optional[object]]] = {}


def register_hook(name: str, fn: Callable[[object], Optional[object]]) -> None:
    """Register a hook function under *name* for use in configs."""
    if not callable(fn):
        raise TypeError(f"Hook '{name}' must be callable")
    _REGISTRY[name] = fn


def presend_hook_config_from_dict(data: dict) -> PresendHookConfig:
    """Build a :class:`PresendHookConfig` from a raw config mapping."""
    hook_name = data.get("hook_name")
    if not hook_name:
        raise ValueError("presend hook config requires 'hook_name'")
    return PresendHookConfig(hook_name=hook_name)


def wrap_with_presend_hook(inner, config: PresendHookConfig) -> PresendHookNotifier:
    """Wrap *inner* with a :class:`PresendHookNotifier` using the named hook."""
    hook_fn = _REGISTRY.get(config.hook_name)
    if hook_fn is None:
        raise KeyError(
            f"No hook registered under '{config.hook_name}'. "
            f"Available: {list(_REGISTRY)}"
        )
    return PresendHookNotifier(inner=inner, hook=hook_fn)
