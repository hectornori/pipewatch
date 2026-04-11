"""Notifier that only forwards alerts when a predicate is satisfied."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


Predicate = Callable[[object], bool]


@dataclass
class ConditionalNotifier:
    """Wraps an inner notifier and only calls it when *predicate* returns True.

    This is useful for routing alerts based on arbitrary runtime conditions,
    e.g. only alerting on failures whose error message matches a pattern, or
    only forwarding when a feature flag is enabled.

    Parameters
    ----------
    inner:
        The downstream notifier to delegate to.
    predicate:
        A callable that receives the result object and returns ``True`` when
        the notification should be forwarded.
    skip_log:
        Optional label used in debug logging to identify this gate.  Defaults
        to the empty string which suppresses the extra log line.
    """

    inner: Notifier
    predicate: Predicate
    skip_log: str = field(default="")

    def send(self, result: object) -> None:  # noqa: D401
        """Forward *result* to the inner notifier only when the predicate passes."""
        import logging

        if self.predicate(result):
            self.inner.send(result)
        else:
            if self.skip_log:
                logging.getLogger(__name__).debug(
                    "ConditionalNotifier[%s]: predicate failed, skipping notification",
                    self.skip_log,
                )


def failures_only() -> Predicate:
    """Return a predicate that passes only when *result.success* is False."""

    def _pred(result: object) -> bool:
        return not getattr(result, "success", True)

    return _pred


def pipeline_name_matches(*names: str) -> Predicate:
    """Return a predicate that passes when the result's pipeline name is in *names*."""
    name_set = frozenset(names)

    def _pred(result: object) -> bool:
        return getattr(result, "pipeline_name", None) in name_set

    return _pred
