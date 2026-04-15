"""Configuration helpers for TaggedNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pipewatch.notifiers.tagged_notifier import TaggedNotifier


@dataclass
class TaggedNotifierConfig:
    """Validated configuration for :class:`TaggedNotifier`."""

    tags: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.tags, dict):
            raise TypeError("tags must be a dict")
        for k, v in self.tags.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise TypeError(f"tag keys and values must be strings, got {k!r}: {v!r}")
            if not k.strip():
                raise ValueError("tag keys must not be blank")


def tagged_notifier_config_from_dict(raw: dict[str, Any]) -> TaggedNotifierConfig:
    """Parse a raw config dict into a :class:`TaggedNotifierConfig`."""
    tags = raw.get("tags", {})
    if not isinstance(tags, dict):
        raise TypeError("'tags' must be a mapping")
    return TaggedNotifierConfig(tags={str(k): str(v) for k, v in tags.items()})


def wrap_with_tags(inner: Any, raw: dict[str, Any]) -> TaggedNotifier:
    """Convenience factory: parse *raw* and return a wrapped notifier."""
    cfg = tagged_notifier_config_from_dict(raw)
    return TaggedNotifier(inner=inner, tags=cfg.tags)
