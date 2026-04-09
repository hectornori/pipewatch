"""Tests for PipelineMonitor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipewatch.monitor import CheckResult, PipelineMonitor
from pipewatch.config import Config, PipelineConfig, SlackConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def pipeline_ok() -> PipelineConfig:
    return PipelineConfig(
        name="orders",
        check_command="exit 0",
        enabled=True,
        timeout_seconds=10,
    )


@pytest.fixture()
def pipeline_fail() -> PipelineConfig:
    return PipelineConfig(
        name="payments",
        check_command="exit 1",
        enabled=True,
        timeout_seconds=10,
    )


@pytest.fixture()
def config_no_notifiers(pipeline_ok, pipeline_fail) -> Config:
    return Config(pipelines=[pipeline_ok, pipeline_fail], slack=None, email=None)


@pytest.fixture()
def config_with_slack(pipeline_fail) -> Config:
    slack = SlackConfig(webhook_url="https://hooks.slack.com/test", channel="#alerts")
    return Config(pipelines=[pipeline_fail], slack=slack, email=None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_check_success(pipeline_ok, config_no_notifiers):
    monitor = PipelineMonitor(config_no_notifiers)
    result = monitor._check(pipeline_ok)
    assert result.success is True
    assert result.exit_code == 0
    assert result.pipeline_name == "orders"


def test_check_failure(pipeline_fail, config_no_notifiers):
    monitor = PipelineMonitor(config_no_notifiers)
    result = monitor._check(pipeline_fail)
    assert result.success is False
    assert result.exit_code == 1


def test_check_timeout(config_no_notifiers):
    slow = PipelineConfig(
        name="slow", check_command="sleep 60", enabled=True, timeout_seconds=1
    )
    monitor = PipelineMonitor(config_no_notifiers)
    result = monitor._check(slow)
    assert result.success is False
    assert result.exit_code == -1
    assert "Timed out" in result.stderr


def test_run_all_returns_all_results(config_no_notifiers):
    monitor = PipelineMonitor(config_no_notifiers)
    results = monitor.run_all()
    assert len(results) == 2


def test_alert_dispatched_on_failure(config_with_slack):
    monitor = PipelineMonitor(config_with_slack)
    monitor._slack = MagicMock()
    monitor.run_all()
    monitor._slack.send.assert_called_once()
    call_kwargs = monitor._slack.send.call_args.kwargs
    assert call_kwargs["pipeline_name"] == "payments"


def test_no_alert_on_success(pipeline_ok, config_with_slack):
    config_with_slack.pipelines = [pipeline_ok]
    monitor = PipelineMonitor(config_with_slack)
    monitor._slack = MagicMock()
    monitor.run_all()
    monitor._slack.send.assert_not_called()


def test_check_result_error_message_none_when_no_stderr(pipeline_ok, config_no_notifiers):
    monitor = PipelineMonitor(config_no_notifiers)
    result = monitor._check(pipeline_ok)
    assert result.error_message is None
