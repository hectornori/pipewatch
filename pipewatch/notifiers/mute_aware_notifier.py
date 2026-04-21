"""Notifier that suppresses alerts when a pipeline is muted."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from pipewatch.mute_manager import MuteManager

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class MuteAwareNotifier:
    """Wraps an inner notifier and skips delivery when the pipeline is muted.

    The ``result`` object is expected to expose a ``pipeline_name`` attribute.
    Any result that does not carry that attribute is forwarded unconditionally.
    """

    inner: Notifier
    mute_manager: MuteManager

    def send(self, result: object) -> None:
        pipeline_name: str | None = getattr(result, "pipeline_name", None)

        if pipeline_name is not None and self.mute_manager.is_muted(pipeline_name):
            logger.debug(
                "MuteAwareNotifier: skipping alert for muted pipeline %r",
                pipeline_name,
            )
            return

        self.inner.send(result)
