"""Send digest reports via configured notifiers."""
from __future__ import annotations

import logging
from typing import List

from pipewatch.config import Config
from pipewatch.digest import DigestReport
from pipewatch.notifiers.slack import SlackNotifier
from pipewatch.notifiers.email import EmailNotifier

logger = logging.getLogger(__name__)


class DigestSender:
    """Dispatches a DigestReport to all enabled notification channels."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._slack: SlackNotifier | None = (
            SlackNotifier(config.slack) if config.slack else None
        )
        self._email: EmailNotifier | None = (
            EmailNotifier(config.email) if config.email else None
        )

    def send(self, digest: DigestReport) -> None:
        """Send the digest to all configured notifiers."""
        subject = (
            f"PipeWatch Digest: {digest.failed} failure(s) in {digest.total} pipeline(s)"
        )
        body = digest.to_text()

        if self._slack:
            try:
                self._slack.send(
                    pipeline_name="digest",
                    message=body,
                    error=None,
                )
                logger.info("Digest sent via Slack.")
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to send digest via Slack: %s", exc)

        if self._email:
            try:
                self._email.send(
                    pipeline_name="digest",
                    message=body,
                    error=None,
                )
                logger.info("Digest sent via email.")
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to send digest via email: %s", exc)

        if not self._slack and not self._email:
            logger.warning("Digest generated but no notifiers are configured.")
