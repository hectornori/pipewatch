"""HTTP webhook notifier — POSTs a JSON payload to a configured URL."""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class WebhookNotifier:
    """Send pipeline check results to an HTTP webhook endpoint."""

    url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout: int = 10

    def send(self, result: object) -> None:
        payload = self._build_payload(result)
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json", **self.headers},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout):
                logger.debug("Webhook delivered to %s", self.url)
        except urllib.error.HTTPError as exc:
            logger.error("Webhook HTTP error %s for %s", exc.code, self.url)
            raise
        except urllib.error.URLError as exc:
            logger.error("Webhook connection error for %s: %s", self.url, exc.reason)
            raise

    def _build_payload(self, result: object) -> dict:
        pipeline = getattr(result, "pipeline_name", "unknown")
        success = getattr(result, "success", None)
        error = getattr(result, "error_message", None)
        return {
            "pipeline": pipeline,
            "success": success,
            "error": error,
        }
