"""ShadowNotifier: forwards to a primary notifier and silently mirrors to a shadow
notifier for comparison / dark-launch testing purposes."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


class Notifier:
    """Structural protocol – any object with a ``send`` method qualifies."""
    def send(self, result: Any) -> None: ...


@dataclass
class ShadowNotifier:
    """Sends via *primary* and mirrors the same result to *shadow*.

    Failures in the shadow notifier are caught and logged so they never
    affect the primary delivery path.
    """
    primary: Notifier
    shadow: Notifier
    _shadow_errors: list[Exception] = field(default_factory=list, init=False, repr=False)

    def send(self, result: Any) -> None:
        """Forward to primary (raises on failure) then mirror to shadow."""
        self.primary.send(result)
        self._mirror(result)

    def _mirror(self, result: Any) -> None:
        try:
            self.shadow.send(result)
        except Exception as exc:  # noqa: BLE001
            self._shadow_errors.append(exc)
            logger.warning(
                "ShadowNotifier: shadow delivery failed for pipeline '%s': %s",
                getattr(result, "pipeline_name", "<unknown>"),
                exc,
            )

    @property
    def shadow_error_count(self) -> int:
        return len(self._shadow_errors)
