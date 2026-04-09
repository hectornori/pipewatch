"""AlertManager — evaluate alert rules and dispatch notifications.

Now integrates DeduplicationStore so identical alerts are not re-sent
within the configured dedup window.
"""

from __future__ import annotations

from typing import List, Optional

from pipewatch.alert_rules import AlertRule
from pipewatch.config import Config
from pipewatch.deduplication import DeduplicationStore
from pipewatch.history import CheckHistory
from pipewatch.monitor import CheckResult
from pipewatch.notifiers.slack import SlackNotifier


class AlertManager:
    """Evaluates alert rules against recent history and dispatches alerts."""

    def __init__(
        self,
        config: Config,
        history: CheckHistory,
        rules: Optional[List[AlertRule]] = None,
        dedup_store: Optional[DeduplicationStore] = None,
    ) -> None:
        self._config = config
        self._history = history
        self._rules: List[AlertRule] = rules or [AlertRule()]
        self._dedup = dedup_store or DeduplicationStore(
            window_seconds=config.dedup_window_seconds
            if hasattr(config, "dedup_window_seconds")
            else 3600
        )

    def evaluate(self, result: CheckResult) -> None:
        """Check rules for *result* and dispatch if warranted and not a duplicate."""
        recent = self._history.get_recent(result.pipeline_name, limit=10)
        for rule in self._rules:
            if not rule.applies_to(result.pipeline_name):
                continue
            if rule.should_alert(recent):
                alert_key = DeduplicationStore.make_key(
                    result.pipeline_name, result.error_message
                )
                if self._dedup.is_duplicate(alert_key):
                    return
                self._dispatch(result)
                self._dedup.record(alert_key)
                return

    def _dispatch(self, result: CheckResult) -> None:
        """Send notifications via all configured notifiers."""
        pipeline_cfg = next(
            (p for p in self._config.pipelines if p.name == result.pipeline_name),
            None,
        )
        if pipeline_cfg is None:
            return

        if self._config.slack and getattr(pipeline_cfg, "notify_slack", True):
            notifier = SlackNotifier(self._config.slack)
            notifier.send(result)
