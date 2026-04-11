"""Tests for AuditedNotifier decorator."""
import pytest
from unittest.mock import MagicMock

from pipewatch.audit_log import AuditLog
from pipewatch.monitor import CheckResult
from pipewatch.notifiers.audited_notifier import AuditedNotifier


@pytest.fixture
def audit_log(tmp_path):
    return AuditLog(db_path=str(tmp_path / "audit.db"))


@pytest.fixture
def _ok_result():
    return CheckResult(pipeline_name="pipe_a", ok=True, error_message=None)


@pytest.fixture
def _fail_result():
    return CheckResult(pipeline_name="pipe_a", ok=False, error_message="timeout")


def test_send_forwards_to_inner(audit_log, _ok_result):
    inner = MagicMock()
    notifier = AuditedNotifier(inner, audit_log, channel="slack")
    notifier.send(_ok_result)
    inner.send.assert_called_once_with(_ok_result)


def test_send_records_audit_entry(audit_log, _ok_result):
    inner = MagicMock()
    notifier = AuditedNotifier(inner, audit_log, channel="slack")
    notifier.send(_ok_result)
    entries = audit_log.get_recent("pipe_a")
    assert len(entries) == 1
    assert entries[0].event_type == "alert"
    assert "slack" in entries[0].detail
    assert "sent" in entries[0].detail


def test_send_records_failure_result(audit_log, _fail_result):
    inner = MagicMock()
    notifier = AuditedNotifier(inner, audit_log, channel="email")
    notifier.send(_fail_result)
    entries = audit_log.get_recent("pipe_a")
    assert "ok=False" in entries[0].detail
    assert "timeout" in entries[0].detail


def test_send_records_even_when_inner_raises(audit_log, _ok_result):
    inner = MagicMock()
    inner.send.side_effect = RuntimeError("connection refused")
    notifier = AuditedNotifier(inner, audit_log, channel="slack")
    with pytest.raises(RuntimeError):
        notifier.send(_ok_result)
    entries = audit_log.get_recent("pipe_a")
    assert len(entries) == 1
    assert "failed" in entries[0].detail


def test_channel_appears_in_detail(audit_log, _ok_result):
    inner = MagicMock()
    notifier = AuditedNotifier(inner, audit_log, channel="pagerduty")
    notifier.send(_ok_result)
    entries = audit_log.get_recent("pipe_a")
    assert "pagerduty" in entries[0].detail
