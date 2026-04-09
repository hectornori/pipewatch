"""Tests for digest report generation and sending."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.digest import DigestReport, build_digest
from pipewatch.monitor import CheckResult
from pipewatch.notifiers.digest_sender import DigestSender


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def ok_result() -> CheckResult:
    return CheckResult(pipeline_name="pipe_ok", success=True, error_message=None)


@pytest.fixture()
def fail_result() -> CheckResult:
    return CheckResult(pipeline_name="pipe_fail", success=False, error_message="timeout")


# ---------------------------------------------------------------------------
# DigestReport unit tests
# ---------------------------------------------------------------------------

def test_digest_counts(ok_result, fail_result):
    report = build_digest([ok_result, fail_result])
    assert report.total == 2
    assert report.passed == 1
    assert report.failed == 1


def test_digest_failure_rate_zero_when_empty():
    report = build_digest([])
    assert report.failure_rate == 0.0


def test_digest_failure_rate(ok_result, fail_result):
    report = build_digest([ok_result, fail_result])
    assert report.failure_rate == pytest.approx(0.5)


def test_digest_failed_results(ok_result, fail_result):
    report = build_digest([ok_result, fail_result])
    assert report.failed_results() == [fail_result]


def test_digest_to_text_contains_summary(ok_result, fail_result):
    report = build_digest([ok_result, fail_result])
    text = report.to_text()
    assert "PipeWatch Digest" in text
    assert "pipe_fail" in text
    assert "timeout" in text
    assert "pipe_ok" not in text  # passed pipelines not listed


def test_digest_to_text_no_failures(ok_result):
    report = build_digest([ok_result])
    text = report.to_text()
    assert "Failed pipelines" not in text


# ---------------------------------------------------------------------------
# DigestSender tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_config_with_slack():
    cfg = MagicMock()
    cfg.slack = MagicMock()
    cfg.email = None
    return cfg


@pytest.fixture()
def mock_config_no_notifiers():
    cfg = MagicMock()
    cfg.slack = None
    cfg.email = None
    return cfg


def test_digest_sender_calls_slack(mock_config_with_slack, ok_result, fail_result):
    with patch("pipewatch.notifiers.digest_sender.SlackNotifier") as MockSlack:
        instance = MockSlack.return_value
        sender = DigestSender(mock_config_with_slack)
        digest = build_digest([ok_result, fail_result])
        sender.send(digest)
        instance.send.assert_called_once()


def test_digest_sender_no_notifiers_logs_warning(
    mock_config_no_notifiers, ok_result, caplog
):
    import logging
    with caplog.at_level(logging.WARNING, logger="pipewatch.notifiers.digest_sender"):
        sender = DigestSender(mock_config_no_notifiers)
        digest = build_digest([ok_result])
        sender.send(digest)
    assert "no notifiers" in caplog.text.lower()
