"""Notifier wrapper that appends runbook links to alert messages."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pipewatch.monitor import CheckResult
from pipewatch.runbook import RunbookStore


class Notifier(Protocol):
    """Structural protocol matching SlackNotifier / EmailNotifier."""

    def send(self, result: CheckResult, extra_message: str = "") -> None:
        ...


@dataclass
class RunbookEnrichedNotifier:
    """Wraps another notifier and appends a runbook link when available.

    Parameters
    ----------
    inner:
        The underlying notifier (Slack, email, etc.) to delegate to.
    runbook_store:
        Store used to look up runbook entries by pipeline name.
    """

    inner: Notifier
    runbook_store: RunbookStore

    def send(self, result: CheckResult, extra_message: str = "") -> None:
        runbook_text = self.runbook_store.format_for_alert(result.pipeline_name)
        if runbook_text:
            combined = f"{extra_message}\n{runbook_text}".strip() if extra_message else runbook_text
        else:
            combined = extra_message
        self.inner.send(result, combined)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def register(self, pipeline_name: str, url: str, description: str = "") -> None:
        """Register or update a runbook entry directly on the notifier."""
        from pipewatch.runbook import RunbookEntry

        self.runbook_store.upsert(
            RunbookEntry(pipeline_name=pipeline_name, url=url, description=description)
        )
