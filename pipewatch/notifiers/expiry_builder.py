"""Builder helper that wires ExpiryNotifier from a raw config dict."""
from __future__ import annotations

from pipewatch.expiry_config import expiry_config_from_dict, wrap_with_expiry
from pipewatch.notifiers.expiry_notifier import Notifier


def build_expiry_notifier(inner: Notifier, raw: dict) -> Notifier:
    """Construct an :class:`ExpiryNotifier` from *inner* and a raw config dict.

    Expected keys in *raw*:
      - ``ttl_seconds`` (required): float, seconds until alerts are suppressed.
      - ``db_path`` (optional): path to the SQLite database file.

    Example::

        notifier = build_expiry_notifier(
            inner=slack_notifier,
            raw={"ttl_seconds": 3600, "db_path": "/var/lib/pipewatch/expiry.db"},
        )
    """
    cfg = expiry_config_from_dict(raw)
    return wrap_with_expiry(inner, cfg)
