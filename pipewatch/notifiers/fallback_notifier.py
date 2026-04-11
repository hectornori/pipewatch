"""FallbackNotifier — tries a primary notifier and falls back to a secondary on failure."""
from __future__ import annotations

import logging
from typing import Protocol

from pipewatch.monitor import CheckResult

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class FallbackNotifier:
    """Sends via *primary*; if that raises, attempts *fallback*.

    This is useful when, for example, Slack is the preferred channel but
    email should be used if the Slack webhook is unreachable.
    """

    def __init__(self, primary: Notifier, fallback: Notifier) -> None:
        self._primary = primary
        self._fallback = fallback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, result: CheckResult) -> None:
        """Attempt primary; on any exception attempt fallback."""
        try:
            self._primary.send(result)
            logger.debug(
                "FallbackNotifier: primary succeeded for pipeline '%s'",
                result.pipeline_name,
            )
        except Exception as primary_exc:  # noqa: BLE001
            logger.warning(
                "FallbackNotifier: primary failed for pipeline '%s' (%s); "
                "attempting fallback.",
                result.pipeline_name,
                primary_exc,
            )
            try:
                self._fallback.send(result)
                logger.debug(
                    "FallbackNotifier: fallback succeeded for pipeline '%s'",
                    result.pipeline_name,
                )
            except Exception as fallback_exc:  # noqa: BLE001
                logger.error(
                    "FallbackNotifier: fallback also failed for pipeline '%s' (%s).",
                    result.pipeline_name,
                    fallback_exc,
                )
                raise fallback_exc from primary_exc
