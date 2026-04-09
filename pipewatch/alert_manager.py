"""Evaluates alert rules against recent history and dispatches notifications."""
from __future__ import annotations

import logging
from typing import List, Optional

from pipewatch.alert_rules import AlertRule
from pipewatch.history import CheckHistory
from pipewatch.monitor import CheckResult
from pipewatch.notifiers.slack import SlackNotifier
from pipewatch.notifiers.email import EmailNotifier
from pipewatch.config import Config

logger = logging.getLogger(__name__)


class AlertManager:
    """Checks alert rules and fires notifiers when conditions are met."""

    def __init__(
        self,
        rules: List[AlertRule],
        history: CheckHistory,
        config: Config,
        lookback: int = 10,
    ) -> None:
        self._rules = rules
        self._history = history
        self._config = config
        self._lookback = lookback
        self._slack: Optional[SlackNotifier] = (
            SlackNotifier(config.slack) if config.slack and config.slack.enabled else None
        )
        self._email: Optional[EmailNotifier] = (
            EmailNotifier(config.email) if config.email and config.email.enabled else None
        )

    def evaluate(self, result: CheckResult) -> None:
        """Evaluate all applicable rules for a freshly-recorded result."""
        recent = self._history.get_recent(result.pipeline_name, limit=self._lookback)
        for rule in self._rules:
            if not rule.applies_to(result.pipeline_name):
                continue
            if rule.should_alert(recent):
                logger.info(
                    "Alert rule '%s' triggered for pipeline '%s'",
                    rule.name,
                    result.pipeline_name,
                )
                self._dispatch(rule, result)

    def _dispatch(self, rule: AlertRule, result: CheckResult) -> None:
        """Send notifications via all configured notifiers."""
        subject = f"[pipewatch] Alert: {rule.name} — {result.pipeline_name}"
        body = (
            f"Alert rule '{rule.name}' was triggered for pipeline "
            f"'{result.pipeline_name}'.\n"
            f"Last error: {result.error_message or 'N/A'}"
        )
        if self._slack:
            try:
                self._slack.send(result)
            except Exception as exc:  # pragma: no cover
                logger.error("Slack notification failed: %s", exc)
        if self._email:
            try:
                self._email.send(result)
            except Exception as exc:  # pragma: no cover
                logger.error("Email notification failed: %s", exc)
