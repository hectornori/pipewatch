from unittest.mock import MagicMock, patch

import pytest

from pipewatch.config import EmailConfig, SlackConfig
from pipewatch.notifiers.email import EmailNotifier
from pipewatch.notifiers.slack import SlackNotifier


# ---------------------------------------------------------------------------
# SlackNotifier tests
# ---------------------------------------------------------------------------

@pytest.fixture
def slack_config():
    return SlackConfig(
        webhook_url="https://hooks.slack.com/services/TEST",
        channel="#alerts",
        username="pipewatch-bot",
        icon_emoji=":fire:",
    )


def test_slack_send_success(slack_config):
    with patch("pipewatch.notifiers.slack.requests") as mock_requests:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response
        mock_requests.RequestException = Exception

        notifier = SlackNotifier(slack_config)
        result = notifier.send("my_pipeline", "Job timed out.", error="TimeoutError")

    assert result is True
    mock_requests.post.assert_called_once()
    call_kwargs = mock_requests.post.call_args
    payload = call_kwargs.kwargs["json"]
    assert "my_pipeline" in payload["text"]
    assert "TimeoutError" in payload["text"]
    assert payload["channel"] == "#alerts"


def test_slack_send_failure(slack_config):
    with patch("pipewatch.notifiers.slack.requests") as mock_requests:
        mock_requests.RequestException = Exception
        mock_requests.post.side_effect = Exception("connection refused")

        notifier = SlackNotifier(slack_config)
        result = notifier.send("my_pipeline", "Something broke.")

    assert result is False


def test_slack_payload_no_error(slack_config):
    notifier = SlackNotifier(slack_config)
    payload = notifier._build_payload("etl_job", "Step failed.", error=None)
    assert "etl_job" in payload["text"]
    assert "```" not in payload["text"]


# ---------------------------------------------------------------------------
# EmailNotifier tests
# ---------------------------------------------------------------------------

@pytest.fixture
def email_config():
    return EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        use_tls=True,
        username="user@example.com",
        password="secret",
        from_address="alerts@example.com",
        to_addresses=["ops@example.com", "dev@example.com"],
    )


def test_email_send_success(email_config):
    with patch("pipewatch.notifiers.email.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        notifier = EmailNotifier(email_config)
        result = notifier.send("daily_load", "Row count mismatch.", error="AssertionError")

    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "secret")
    mock_server.sendmail.assert_called_once()


def test_email_send_failure(email_config):
    import smtplib

    with patch("pipewatch.notifiers.email.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp_cls.side_effect = smtplib.SMTPConnectError(421, "Service unavailable")

        notifier = EmailNotifier(email_config)
        result = notifier.send("daily_load", "Connection failed.")

    assert result is False


def test_email_body_includes_error(email_config):
    notifier = EmailNotifier(email_config)
    body = notifier._build_body("pipeline_x", "Unexpected error.", error="KeyError: 'id'")
    assert "pipeline_x" in body
    assert "KeyError: 'id'" in body
