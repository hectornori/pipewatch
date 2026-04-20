"""Builder that constructs a TrendAlertNotifier from raw config dicts."""
from __future__ import annotations

from typing import Any

from pipewatch.trend_alert_config import trend_alert_config_from_dict, wrap_with_trend_alert
from pipewatch.notifiers.trend_alert_notifier import TrendAlertNotifier, Notifier


def build_trend_alert_notifier(
    inner: Notifier,
    raw: dict[str, Any],
) -> TrendAlertNotifier:
    """Build a TrendAlertNotifier from a raw config mapping.

    Example YAML section::

        trend_alert:
          failure_rate_threshold: 0.6
          lookback: 8
          db_path: /var/lib/pipewatch/metrics.db

    Args:
        inner: The downstream notifier to forward to when the trend is bad.
        raw:   Dictionary parsed from the ``trend_alert`` YAML block.

    Returns:
        A configured :class:`TrendAlertNotifier` instance.
    """
    config = trend_alert_config_from_dict(raw)
    return wrap_with_trend_alert(inner, config)
