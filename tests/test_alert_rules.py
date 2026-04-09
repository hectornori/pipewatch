"""Tests for pipewatch.alert_rules."""
import pytest

from pipewatch.alert_rules import AlertRule, rule_from_dict
from pipewatch.monitor import CheckResult


def _result(success: bool, pipeline: str = "pipe") -> CheckResult:
    return CheckResult(
        pipeline_name=pipeline,
        success=success,
        error_message=None if success else "boom",
    )


# ---------------------------------------------------------------------------
# AlertRule construction
# ---------------------------------------------------------------------------

def test_default_rule_creation():
    rule = AlertRule(name="basic")
    assert rule.consecutive_failures == 1
    assert rule.failure_rate_threshold is None
    assert rule.pipelines == []


def test_invalid_consecutive_failures():
    with pytest.raises(ValueError, match="consecutive_failures"):
        AlertRule(name="bad", consecutive_failures=0)


def test_invalid_failure_rate_threshold():
    with pytest.raises(ValueError, match="failure_rate_threshold"):
        AlertRule(name="bad", failure_rate_threshold=1.5)


# ---------------------------------------------------------------------------
# applies_to
# ---------------------------------------------------------------------------

def test_applies_to_all_when_empty():
    rule = AlertRule(name="r")
    assert rule.applies_to("any_pipeline") is True


def test_applies_to_specific_pipeline():
    rule = AlertRule(name="r", pipelines=["pipe_a"])
    assert rule.applies_to("pipe_a") is True
    assert rule.applies_to("pipe_b") is False


# ---------------------------------------------------------------------------
# should_alert — consecutive failures
# ---------------------------------------------------------------------------

def test_no_alert_on_empty_results():
    rule = AlertRule(name="r", consecutive_failures=1)
    assert rule.should_alert([]) is False


def test_alert_on_single_failure():
    rule = AlertRule(name="r", consecutive_failures=1)
    assert rule.should_alert([_result(False)]) is True


def test_no_alert_on_success():
    rule = AlertRule(name="r", consecutive_failures=1)
    assert rule.should_alert([_result(True)]) is False


def test_alert_on_consecutive_failures():
    rule = AlertRule(name="r", consecutive_failures=3)
    results = [_result(True), _result(False), _result(False), _result(False)]
    assert rule.should_alert(results) is True


def test_no_alert_when_not_enough_consecutive():
    rule = AlertRule(name="r", consecutive_failures=3)
    results = [_result(False), _result(False), _result(True)]
    assert rule.should_alert(results) is False


# ---------------------------------------------------------------------------
# should_alert — failure rate
# ---------------------------------------------------------------------------

def test_alert_on_failure_rate_exceeded():
    rule = AlertRule(name="r", consecutive_failures=99, failure_rate_threshold=0.5)
    results = [_result(False), _result(False), _result(True), _result(True)]
    assert rule.should_alert(results) is True  # 50% == threshold


def test_no_alert_below_failure_rate():
    rule = AlertRule(name="r", consecutive_failures=99, failure_rate_threshold=0.6)
    results = [_result(False), _result(True), _result(True), _result(True)]
    assert rule.should_alert(results) is False  # 25% < 60%


# ---------------------------------------------------------------------------
# rule_from_dict
# ---------------------------------------------------------------------------

def test_rule_from_dict_minimal():
    rule = rule_from_dict({"name": "simple"})
    assert rule.name == "simple"
    assert rule.consecutive_failures == 1


def test_rule_from_dict_full():
    data = {
        "name": "strict",
        "consecutive_failures": 2,
        "failure_rate_threshold": 0.4,
        "pipelines": ["etl_main"],
    }
    rule = rule_from_dict(data)
    assert rule.consecutive_failures == 2
    assert rule.failure_rate_threshold == pytest.approx(0.4)
    assert rule.pipelines == ["etl_main"]
