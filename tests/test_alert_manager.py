"""Tests for pipewatch.alert_manager."""
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.alert_manager import AlertManager
from pipewatch.alert_rules import AlertRule
from pipewatch.monitor import CheckResult
from pipewatch.config import Config, SlackConfig, EmailConfig


def _result(success: bool, name: str = "pipe") -> CheckResult:
    return CheckResult(
        pipeline_name=name,
        success=success,
        error_message=None if success else "error!",
    )


@pytest.fixture()
def mock_history():
    h = MagicMock()
    h.get_recent.return_value = [_result(False)]
    return h


@pytest.fixture()
def bare_config():
    return Config(pipelines=[], slack=None, email=None)


@pytest.fixture()
def slack_config():
    return Config(
        pipelines=[],
        slack=SlackConfig(webhook_url="https://hooks.slack.com/x", enabled=True),
        email=None,
    )


# ---------------------------------------------------------------------------
# Evaluate — no notifiers
# ---------------------------------------------------------------------------

def test_no_dispatch_when_rule_not_triggered(mock_history, bare_config):
    mock_history.get_recent.return_value = [_result(True)]
    rule = AlertRule(name="r", consecutive_failures=1)
    manager = AlertManager(rules=[rule], history=mock_history, config=bare_config)
    # Should complete without error
    manager.evaluate(_result(True))


def test_rule_not_applicable_skipped(mock_history, bare_config):
    rule = AlertRule(name="r", pipelines=["other_pipe"])
    manager = AlertManager(rules=[rule], history=mock_history, config=bare_config)
    manager.evaluate(_result(False, name="pipe"))  # rule doesn't apply
    # history still queried
    mock_history.get_recent.assert_called_once()


# ---------------------------------------------------------------------------
# Evaluate — with Slack notifier
# ---------------------------------------------------------------------------

def test_slack_notifier_called_on_alert(mock_history, slack_config):
    rule = AlertRule(name="r", consecutive_failures=1)
    with patch("pipewatch.alert_manager.SlackNotifier") as MockSlack:
        mock_notifier = MagicMock()
        MockSlack.return_value = mock_notifier
        manager = AlertManager(rules=[rule], history=mock_history, config=slack_config)
        manager.evaluate(_result(False))
        mock_notifier.send.assert_called_once()


def test_no_slack_when_disabled(mock_history):
    config = Config(
        pipelines=[],
        slack=SlackConfig(webhook_url="https://hooks.slack.com/x", enabled=False),
        email=None,
    )
    rule = AlertRule(name="r", consecutive_failures=1)
    with patch("pipewatch.alert_manager.SlackNotifier") as MockSlack:
        AlertManager(rules=[rule], history=mock_history, config=config)
        MockSlack.assert_not_called()


# ---------------------------------------------------------------------------
# Lookback respected
# ---------------------------------------------------------------------------

def test_lookback_passed_to_history(mock_history, bare_config):
    rule = AlertRule(name="r")
    manager = AlertManager(
        rules=[rule], history=mock_history, config=bare_config, lookback=5
    )
    manager.evaluate(_result(False, name="pipe"))
    mock_history.get_recent.assert_called_with("pipe", limit=5)
