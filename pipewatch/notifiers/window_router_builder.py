"""Build a WindowNotifier from a unified config dictionary.

Expected config shape::

    window:
      start: "08:00"
      end:   "20:00"
      tz:    "UTC"          # optional
    notifier: slack          # key into a pre-built notifier map
"""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.notifiers.window_notifier import WindowNotifier
from pipewatch.window_config import window_config_from_dict


def build_window_notifier(
    config: Dict[str, Any],
    notifier_map: Dict[str, Any],
) -> WindowNotifier:
    """Construct a :class:`WindowNotifier` from *config* and *notifier_map*.

    Args:
        config:       Raw config dict containing ``window`` and ``notifier`` keys.
        notifier_map: Mapping of notifier names to pre-built notifier instances.

    Returns:
        A configured :class:`WindowNotifier`.

    Raises:
        KeyError: If required keys are absent.
        ValueError: If the window parameters are invalid.
    """
    window_data = config.get("window")
    if not window_data:
        raise KeyError("'window' key is required in window notifier config")

    notifier_key = config.get("notifier")
    if not notifier_key:
        raise KeyError("'notifier' key is required in window notifier config")

    if notifier_key not in notifier_map:
        raise KeyError(
            f"Notifier '{notifier_key}' not found in notifier_map. "
            f"Available: {list(notifier_map)}"
        )

    window_cfg = window_config_from_dict(window_data)
    inner = notifier_map[notifier_key]

    return WindowNotifier(
        inner=inner,
        start=window_cfg.start,
        end=window_cfg.end,
        tz=window_cfg.tz,
    )
