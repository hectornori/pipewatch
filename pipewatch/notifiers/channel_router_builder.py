"""Build a ChannelRouter from a list of route configuration dicts.

Expected config shape (YAML / dict)::

    channel_routes:
      - pattern: "etl_*"
        notifier: slack
      - pattern: "reports_*"
        notifier: email
    channel_default: slack
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pipewatch.notifiers.channel_router import ChannelRouter
from pipewatch.notifiers.slack import SlackNotifier
from pipewatch.notifiers.email import EmailNotifier
from pipewatch.config import Config


_NOTIFIER_REGISTRY: Dict[str, Any] = {}


def _build_notifier_map(config: Config) -> Dict[str, Any]:
    """Construct a name -> notifier mapping from the top-level Config."""
    notifiers: Dict[str, Any] = {}
    if config.slack:
        notifiers["slack"] = SlackNotifier(config.slack)
    if config.email:
        notifiers["email"] = EmailNotifier(config.email)
    return notifiers


def build_channel_router(
    route_configs: List[Dict[str, str]],
    config: Config,
    default_name: Optional[str] = None,
) -> ChannelRouter:
    """Build a ChannelRouter from a list of {pattern, notifier} dicts.

    Args:
        route_configs: List of dicts, each with ``pattern`` and ``notifier`` keys.
        config: Top-level pipewatch Config used to instantiate notifiers.
        default_name: Optional name of the notifier to use as the fallback.

    Returns:
        A configured :class:`ChannelRouter`.

    Raises:
        KeyError: If a referenced notifier name is not available in *config*.
    """
    notifier_map = _build_notifier_map(config)

    default = None
    if default_name:
        if default_name not in notifier_map:
            raise KeyError(
                f"Default notifier '{default_name}' not found in config. "
                f"Available: {list(notifier_map)}"
            )
        default = notifier_map[default_name]

    router = ChannelRouter(default=default)

    for entry in route_configs:
        pattern = entry["pattern"]
        notifier_name = entry["notifier"]
        if notifier_name not in notifier_map:
            raise KeyError(
                f"Notifier '{notifier_name}' referenced in channel_routes not found. "
                f"Available: {list(notifier_map)}"
            )
        router.register(pattern, notifier_map[notifier_name])

    return router
