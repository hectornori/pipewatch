"""Builds a PriorityNotifier from config and a notifier registry."""
from __future__ import annotations

from typing import Any

from pipewatch.priority_config import priority_config_from_dict
from pipewatch.notifiers.priority_notifier import PriorityNotifier


def build_priority_router(
    raw_config: dict[str, Any],
    notifier_map: dict[str, Any],
) -> PriorityNotifier:
    """Construct a :class:`PriorityNotifier` from *raw_config*.

    Parameters
    ----------
    raw_config:
        Dictionary containing ``routes`` (list) and optionally
        ``default_notifier`` (str key into *notifier_map*).
    notifier_map:
        Mapping of notifier name -> notifier instance.  Keys must match the
        ``notifier`` field in each route entry.

    Raises
    ------
    KeyError
        If a notifier name referenced in the config is not present in
        *notifier_map*.
    """
    cfg = priority_config_from_dict(raw_config)
    router = PriorityNotifier()

    for route in cfg.routes:
        name: str = route["notifier"]
        if name not in notifier_map:
            raise KeyError(
                f"Priority route references unknown notifier '{name}'. "
                f"Available: {list(notifier_map)}"
            )
        router.register(
            min_priority=route["min_priority"],
            notifier=notifier_map[name],
        )

    if cfg.default_notifier is not None:
        name = cfg.default_notifier
        if name not in notifier_map:
            raise KeyError(
                f"Default notifier '{name}' not found in notifier map. "
                f"Available: {list(notifier_map)}"
            )
        router.set_default(notifier_map[name])

    return router
