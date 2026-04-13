"""Priority-aware notifier that routes alerts based on a numeric priority level."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result) -> None:
        ...


@dataclass
class PriorityRoute:
    """Maps a minimum priority level to a notifier."""
    min_priority: int
    notifier: Notifier

    def matches(self, priority: int) -> bool:
        return priority >= self.min_priority


@dataclass
class PriorityNotifier:
    """Routes a result to all notifiers whose minimum priority is satisfied.

    Results must expose a ``priority`` attribute (int).  If the attribute is
    absent the priority defaults to 0.
    """
    routes: list[PriorityRoute] = field(default_factory=list)
    _default: Notifier | None = field(default=None, repr=False)

    def register(self, min_priority: int, notifier: Notifier) -> None:
        """Add a route."""
        self.routes.append(PriorityRoute(min_priority=min_priority, notifier=notifier))

    def set_default(self, notifier: Notifier) -> None:
        """Notifier used when no route matches."""
        self._default = notifier

    def send(self, result) -> None:
        priority: int = getattr(result, "priority", 0)
        matched = False
        for route in self.routes:
            if route.matches(priority):
                route.notifier.send(result)
                matched = True
        if not matched and self._default is not None:
            self._default.send(result)
