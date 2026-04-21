"""Builder helper for wiring DigestIntervalNotifier from config dicts."""
from __future__ import annotations

from typing import Any, Dict

from pipewatch.digest_interval_config import DigestIntervalConfig, digest_interval_config_from_dict
from pipewatch.notifiers.digest_interval_notifier import DigestIntervalNotifier


def build_digest_interval_notifier(
    inner,
    raw: Dict[str, Any],
) -> DigestIntervalNotifier:
    """Construct a :class:`DigestIntervalNotifier` wrapping *inner* from *raw* config.

    Parameters
    ----------
    inner:
        The downstream notifier that will receive the flushed digest.
    raw:
        A dict with optional keys ``interval_seconds`` and ``db_path``.
    """
    cfg: DigestIntervalConfig = digest_interval_config_from_dict(raw)
    return DigestIntervalNotifier(
        inner=inner,
        interval_seconds=cfg.interval_seconds,
    )
