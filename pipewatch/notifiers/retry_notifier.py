"""Notifier wrapper that retries delivery on failure using RetryPolicy."""

from __future__ import annotations

import logging
from typing import Protocol

from pipewatch.monitor import CheckResult
from pipewatch.retry import RetryPolicy, policy_from_dict

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class RetryNotifier:
    """Wraps an inner notifier and retries on exception according to a RetryPolicy."""

    def __init__(self, inner: Notifier, policy: RetryPolicy | None = None) -> None:
        self._inner = inner
        self._policy = policy or RetryPolicy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, result: CheckResult) -> None:
        """Attempt to send via the inner notifier, retrying on failure."""
        attempt = 0
        last_exc: Exception | None = None

        def _do_send() -> None:
            self._inner.send(result)

        try:
            self._policy.with_retry(_do_send)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "RetryNotifier: all attempts exhausted for pipeline '%s': %s",
                result.pipeline_name,
                exc,
            )
            raise


def retry_notifier_from_dict(inner: Notifier, cfg: dict) -> RetryNotifier:
    """Build a RetryNotifier from a plain config dict."""
    policy = policy_from_dict(cfg)
    return RetryNotifier(inner=inner, policy=policy)
