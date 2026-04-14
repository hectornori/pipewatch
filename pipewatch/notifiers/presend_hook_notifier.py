"""Notifier wrapper that runs a pre-send hook before forwarding.

The hook receives the CheckResult and may mutate or replace it before
the inner notifier is called.  If the hook raises, the send is aborted
and the exception is re-raised.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

log = logging.getLogger(__name__)


class Notifier:
    """Structural protocol satisfied by all pipewatch notifiers."""

    def send(self, result) -> None:  # pragma: no cover
        ...


HookFn = Callable[[object], Optional[object]]


@dataclass
class PresendHookNotifier:
    """Runs *hook* on the result before forwarding to *inner*.

    If the hook returns a non-None value it is used as the result passed
    to the inner notifier; otherwise the original result is forwarded.
    If the hook raises, the notification is skipped and the exception
    propagates to the caller.
    """

    inner: Notifier
    hook: HookFn
    _hooks: list[HookFn] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._hooks = [self.hook]

    def register_hook(self, fn: HookFn) -> None:
        """Append an additional hook to the chain."""
        self._hooks.append(fn)

    def send(self, result) -> None:
        current = result
        for hook in self._hooks:
            replacement = hook(current)
            if replacement is not None:
                current = replacement
        log.debug("PresendHookNotifier forwarding after %d hook(s)", len(self._hooks))
        self.inner.send(current)
