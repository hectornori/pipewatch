"""Route notifications to different notifiers based on pipeline name patterns."""
from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Protocol, runtime_checkable

from pipewatch.monitor import CheckResult

logger = logging.getLogger(__name__)


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


@dataclass
class ChannelRoute:
    """A single routing rule: if pipeline name matches pattern, use notifier."""
    pattern: str
    notifier: Notifier

    def matches(self, pipeline_name: str) -> bool:
        """Return True if the pipeline name matches the glob pattern."""
        return fnmatch.fnmatch(pipeline_name, self.pattern)


@dataclass
class ChannelRouter:
    """Route a CheckResult to the first matching notifier, or fall back to default."""
    routes: List[ChannelRoute] = field(default_factory=list)
    default: Optional[Notifier] = None

    def register(self, pattern: str, notifier: Notifier) -> None:
        """Add a routing rule."""
        self.routes.append(ChannelRoute(pattern=pattern, notifier=notifier))

    def send(self, result: CheckResult) -> None:
        """Dispatch result to the first matching route, or default if none match."""
        for route in self.routes:
            if route.matches(result.pipeline_name):
                logger.debug(
                    "ChannelRouter: routing '%s' via pattern '%s'",
                    result.pipeline_name,
                    route.pattern,
                )
                route.notifier.send(result)
                return

        if self.default is not None:
            logger.debug(
                "ChannelRouter: no pattern matched '%s', using default notifier",
                result.pipeline_name,
            )
            self.default.send(result)
        else:
            logger.debug(
                "ChannelRouter: no pattern matched '%s' and no default configured",
                result.pipeline_name,
            )
