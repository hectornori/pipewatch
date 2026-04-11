"""Routes notifications to different notifiers based on alert severity."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


SEVERITY_LEVELS = ("critical", "high", "medium", "low")


@dataclass
class SeverityRoute:
    severity: str
    notifier: Notifier

    def __post_init__(self) -> None:
        if self.severity not in SEVERITY_LEVELS:
            raise ValueError(
                f"Invalid severity {self.severity!r}. "
                f"Must be one of: {SEVERITY_LEVELS}"
            )

    def matches(self, result: object) -> bool:
        return getattr(result, "severity", None) == self.severity


@dataclass
class SeverityRouter:
    """Dispatch a result to the first route whose severity matches.

    Falls back to *default* if no route matches (or if default is None,
    the result is silently dropped).
    """

    routes: list[SeverityRoute] = field(default_factory=list)
    default: Notifier | None = None

    def register(self, severity: str, notifier: Notifier) -> None:
        """Add a severity → notifier mapping."""
        self.routes.append(SeverityRoute(severity=severity, notifier=notifier))

    def send(self, result: object) -> None:
        for route in self.routes:
            if route.matches(result):
                route.notifier.send(result)
                return
        if self.default is not None:
            self.default.send(result)
