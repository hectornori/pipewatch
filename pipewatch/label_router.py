"""Route alerts to different notifiers based on pipeline labels/tags."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.monitor import CheckResult


class Notifier:
    """Structural interface for notifiers."""

    def send(self, result: CheckResult) -> None:  # pragma: no cover
        raise NotImplementedError


@dataclass
class LabelRoute:
    """A single routing rule: if a pipeline carries *label*, send to *notifier*."""

    label: str
    notifier: Notifier

    def matches(self, result: CheckResult) -> bool:
        """Return True when the pipeline result carries this route's label."""
        tags: List[str] = getattr(result.pipeline, "tags", []) or []
        return self.label in tags


@dataclass
class LabelRouter:
    """Dispatch a CheckResult to every notifier whose label matches the pipeline.

    Routes are evaluated in order; a single result may be dispatched to
    multiple notifiers if several labels match.  An optional *default*
    notifier receives results that match no route.
    """

    routes: List[LabelRoute] = field(default_factory=list)
    default: Optional[Notifier] = None

    def add_route(self, label: str, notifier: Notifier) -> None:
        """Append a new label → notifier mapping."""
        self.routes.append(LabelRoute(label=label, notifier=notifier))

    def dispatch(self, result: CheckResult) -> None:
        """Send *result* to all matching notifiers (or the default if none match)."""
        matched = False
        for route in self.routes:
            if route.matches(result):
                route.notifier.send(result)
                matched = True
        if not matched and self.default is not None:
            self.default.send(result)

    def dispatch_all(self, results: List[CheckResult]) -> None:
        """Convenience wrapper to dispatch a list of results."""
        for result in results:
            self.dispatch(result)
