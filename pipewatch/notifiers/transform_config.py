"""Configuration helpers for building :class:`PayloadTransformer` instances
from a YAML/dict config block.

Supported built-in transform names
-----------------------------------
``add_env_tag``
    Appends the value of *env* (default ``"production"``) to ``result.tags``.
``redact_error``
    Replaces ``result.error_message`` with ``"[REDACTED]"``.
``identity``
    No-op; returns the result unchanged.
"""
from __future__ import annotations

from typing import Callable

from pipewatch.notifiers.payload_transformer import Notifier, PayloadTransformer


_BUILTIN_TRANSFORMS: dict[str, Callable[..., Callable[[object], object]]] = {}


def _register(name: str):
    def decorator(fn):
        _BUILTIN_TRANSFORMS[name] = fn
        return fn
    return decorator


@_register("identity")
def _identity_factory(**_kwargs) -> Callable[[object], object]:
    return lambda result: result


@_register("add_env_tag")
def _add_env_tag_factory(env: str = "production", **_kwargs) -> Callable[[object], object]:
    def _transform(result: object) -> object:
        tags = getattr(result, "tags", None)
        if isinstance(tags, list):
            tags.append(env)
        return result
    return _transform


@_register("redact_error")
def _redact_error_factory(**_kwargs) -> Callable[[object], object]:
    def _transform(result: object) -> object:
        if hasattr(result, "error_message"):
            object.__setattr__(result, "error_message", "[REDACTED]")
        return result
    return _transform


def build_transform(name: str, **options) -> Callable[[object], object]:
    """Return a transform callable by *name*, passing *options* as kwargs.

    Raises
    ------
    ValueError
        If *name* is not a registered built-in transform.
    """
    if name not in _BUILTIN_TRANSFORMS:
        available = ", ".join(sorted(_BUILTIN_TRANSFORMS))
        raise ValueError(
            f"Unknown transform {name!r}. Available: {available}"
        )
    return _BUILTIN_TRANSFORMS[name](**options)


def list_transforms() -> list[str]:
    """Return a sorted list of all registered built-in transform names.

    Useful for introspection and generating help/documentation at runtime.

    Returns
    -------
    list[str]
        Sorted list of transform names, e.g. ``['add_env_tag', 'identity', 'redact_error']``.
    """
    return sorted(_BUILTIN_TRANSFORMS)


def wrap_with_transform(inner: Notifier, config: dict) -> PayloadTransformer:
    """Build a :class:`PayloadTransformer` from a config dict.

    Expected keys:
        - ``transform`` (str): name of the built-in transform.
        - ``options`` (dict, optional): keyword arguments forwarded to the
          transform factory.
        - ``fallback_on_error`` (bool, optional, default ``True``).
    """
    name: str = config["transform"]
    options: dict = config.get("options", {})
    fallback: bool = config.get("fallback_on_error", True)
    fn = build_transform(name, **options)
    return PayloadTransformer(inner=inner, transform=fn, _fallback_on_error=fallback)
