"""Sends notifications on incident open/resolve transitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from pipewatch.incident_tracker import Incident, IncidentTracker
from pipewatch.monitor import CheckResult


class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


@dataclass
class IncidentNotifier:
    """Wraps an IncidentTracker and fires notifications on state transitions."""

    tracker: IncidentTracker
    notifier: Notifier
    resolve_notifier: Optional[Notifier] = None

    def handle(self, result: CheckResult) -> None:
        """Evaluate result and dispatch notifications on open/resolve transitions."""
        pipeline_name = result.pipeline_name

        if result.success:
            was_open = self.tracker.resolve(pipeline_name)
            if was_open and self.resolve_notifier is not None:
                self.resolve_notifier.send(result)
        else:
            already_open = self.tracker.has_open(pipeline_name)
            self.tracker.open_or_update(pipeline_name, result.error_message)
            if not already_open:
                self.notifier.send(result)

    def current_incident(self, pipeline_name: str) -> Optional[Incident]:
        return self.tracker.get_open(pipeline_name)
