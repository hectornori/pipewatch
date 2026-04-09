import logging
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

from pipewatch.config import SlackConfig

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Sends pipeline failure alerts to a Slack channel via webhook."""

    def __init__(self, config: SlackConfig):
        self.config = config

    def send(self, pipeline_name: str, message: str, error: Optional[str] = None) -> bool:
        """Send a Slack notification for a pipeline failure.

        Returns True if the message was sent successfully, False otherwise.
        """
        if requests is None:
            logger.error("'requests' package is required for Slack notifications.")
            return False

        payload = self._build_payload(pipeline_name, message, error)
        try:
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Slack notification sent for pipeline '%s'.", pipeline_name)
            return True
        except requests.RequestException as exc:
            logger.error("Failed to send Slack notification: %s", exc)
            return False

    def _build_payload(self, pipeline_name: str, message: str, error: Optional[str]) -> dict:
        """Build the Slack message payload."""
        channel = self.config.channel
        username = self.config.username or "pipewatch"
        icon_emoji = self.config.icon_emoji or ":warning:"

        text = f":rotating_light: *Pipeline failure: `{pipeline_name}`*\n{message}"
        if error:
            text += f"\n```{error}```"

        payload: dict = {"text": text, "username": username, "icon_emoji": icon_emoji}
        if channel:
            payload["channel"] = channel
        return payload
