"""Tests for pipewatch.escalation."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from pipewatch.escalation import EscalationPolicy, policy_from_dict
from pipewatch.monitor import CheckResult
from pipewatch.suppression import SuppressionStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    db_path = str(tmp_path / "suppression.db")
    return SuppressionStore(db_path=db_path)


@pytest.fixture()
def ok_result():
    return CheckResult(pipeline_name="pipe_ok", success=True, error_message=None)


@pytest.fixture()
def fail_result():
    return CheckResult(pipeline_name="pipe_fail", success=False, error_message="boom")


# ---------------------------------------------------------------------------
# Construction / validation
# ---------------------------------------------------------------------------

def test_default_policy_creation():
    p = EscalationPolicy()
    assert p.escalate_after_minutes == 60
    assert p.max_escalations == 3


def test_invalid_escalate_after_minutes():
    with pytest.raises(ValueError):
        EscalationPolicy(escalate_after_minutes=0)


def test_invalid_max_escalations():
    with pytest.raises(ValueError):
        EscalationPolicy(max_escalations=-1)


def test_policy_from_dict():
    p = policy_from_dict({"escalate_after_minutes": 30, "max_escalations": 5})
    assert p.escalate_after_minutes == 30
    assert p.max_escalations == 5


def test_policy_from_dict_defaults():
    p = policy_from_dict({})
    assert p.escalate_after_minutes == 60
    assert p.max_escalations == 3


# ---------------------------------------------------------------------------
# should_escalate logic
# ---------------------------------------------------------------------------

def test_no_escalation_on_success(store, ok_result):
    policy = EscalationPolicy()
    assert policy.should_escalate(ok_result, store, escalation_count=0) is False


def test_escalate_on_first_failure(store, fail_result):
    policy = EscalationPolicy()
    assert policy.should_escalate(fail_result, store, escalation_count=0) is True


def test_no_escalation_when_max_reached(store, fail_result):
    policy = EscalationPolicy(max_escalations=2)
    assert policy.should_escalate(fail_result, store, escalation_count=2) is False


def test_unlimited_escalations_when_zero(store, fail_result):
    policy = EscalationPolicy(max_escalations=0)
    assert policy.should_escalate(fail_result, store, escalation_count=999) is True


def test_no_escalation_within_cooldown(store, fail_result):
    policy = EscalationPolicy(escalate_after_minutes=60)
    policy.record(fail_result, store)
    # Simulate only 10 minutes passing
    with patch("pipewatch.escalation.datetime") as mock_dt:
        mock_dt.utcnow.return_value = datetime.utcnow() + timedelta(minutes=10)
        result = policy.should_escalate(fail_result, store, escalation_count=1)
    assert result is False


def test_escalation_after_cooldown_elapsed(store, fail_result):
    policy = EscalationPolicy(escalate_after_minutes=60)
    policy.record(fail_result, store)
    with patch("pipewatch.escalation.datetime") as mock_dt:
        mock_dt.utcnow.return_value = datetime.utcnow() + timedelta(minutes=61)
        result = policy.should_escalate(fail_result, store, escalation_count=1)
    assert result is True


def test_record_updates_store(store, fail_result):
    policy = EscalationPolicy()
    assert store.last_alerted_at(fail_result.pipeline_name, namespace="escalation") is None
    policy.record(fail_result, store)
    assert store.last_alerted_at(fail_result.pipeline_name, namespace="escalation") is not None
