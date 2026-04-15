"""SizeGuardNotifier – drops or truncates notifications whose payload
exceeds a configurable byte threshold before forwarding to an inner notifier.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: Any) -> None:
        ...


@dataclass
class SizeGuardNotifier:
    """Wraps an inner notifier and enforces a maximum payload size.

    Args:
        inner:      The downstream notifier to delegate to.
        max_bytes:  Maximum allowed serialised payload size in bytes.
        truncate:   When True, truncate the error_message field instead of
                    dropping the notification entirely.
    """

    inner: Notifier
    max_bytes: int = 4096
    truncate: bool = False

    def __post_init__(self) -> None:
        if self.max_bytes < 1:
            raise ValueError("max_bytes must be a positive integer")

    def send(self, result: Any) -> None:
        payload = self._serialise(result)
        size = len(payload.encode("utf-8"))

        if size <= self.max_bytes:
            self.inner.send(result)
            return

        if self.truncate:
            truncated = self._truncate_result(result, size)
            logger.warning(
                "SizeGuardNotifier: payload for '%s' truncated from %d to fit %d bytes",
                getattr(result, "pipeline_name", "unknown"),
                size,
                self.max_bytes,
            )
            self.inner.send(truncated)
        else:
            logger.warning(
                "SizeGuardNotifier: payload for '%s' dropped – %d bytes exceeds limit of %d",
                getattr(result, "pipeline_name", "unknown"),
                size,
                self.max_bytes,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialise(result: Any) -> str:
        try:
            return json.dumps(
                {
                    "pipeline": getattr(result, "pipeline_name", ""),
                    "success": getattr(result, "success", None),
                    "error": getattr(result, "error_message", ""),
                }
            )
        except (TypeError, ValueError):
            return str(result)

    def _truncate_result(self, result: Any, current_size: int) -> Any:
        """Return a shallow copy of *result* with error_message trimmed."""
        excess = current_size - self.max_bytes
        error = getattr(result, "error_message", "") or ""
        trimmed = error[: max(0, len(error) - excess - 3)] + "..."

        # Build a lightweight wrapper that overrides error_message only.
        class _TrimmedResult:
            def __getattr__(self_, name: str) -> Any:  # noqa: N805
                return getattr(result, name)

            error_message = trimmed

        return _TrimmedResult()
