"""Tests for pipewatch.trend."""
import pytest
from pipewatch.monitor import CheckResult
from pipewatch.trend import TrendSummary, analyse, format_trend


def _r(success: bool, name: str = "pipe") -> CheckResult:
    return CheckResult(
        pipeline_name=name,
        success=success,
        error_message=None if success else "err",
    )


# ---------------------------------------------------------------------------
# analyse()
# ---------------------------------------------------------------------------

def test_empty_results():
    summary = analyse("pipe", [])
    assert summary.total == 0
    assert summary.failures == 0
    assert summary.consecutive_failures == 0
    assert summary.failure_rate == 0.0
    assert summary.is_degrading is False


def test_all_success():
    results = [_r(True)] * 5
    summary = analyse("pipe", results)
    assert summary.failures == 0
    assert summary.consecutive_failures == 0
    assert summary.is_degrading is False


def test_all_failures():
    results = [_r(False)] * 6
    summary = analyse("pipe", results)
    assert summary.failures == 6
    assert summary.consecutive_failures == 6
    assert summary.failure_rate == pytest.approx(1.0)


def test_consecutive_failures_trailing():
    # Two successes then three failures
    results = [_r(True), _r(True), _r(False), _r(False), _r(False)]
    summary = analyse("pipe", results)
    assert summary.consecutive_failures == 3


def test_consecutive_failures_resets_on_success():
    results = [_r(False), _r(False), _r(True), _r(False)]
    summary = analyse("pipe", results)
    assert summary.consecutive_failures == 1


def test_window_limits_results():
    # 20 results but window=5
    results = [_r(False)] * 20
    summary = analyse("pipe", results, window=5)
    assert summary.total == 5
    assert summary.window == 5


def test_degrading_detected():
    # First half mostly ok, second half all failing
    results = [_r(True), _r(True), _r(False), _r(False), _r(False), _r(False)]
    summary = analyse("pipe", results)
    assert summary.is_degrading is True


def test_not_degrading_when_improving():
    # First half mostly failing, second half mostly ok
    results = [_r(False), _r(False), _r(False), _r(True), _r(True), _r(True)]
    summary = analyse("pipe", results)
    assert summary.is_degrading is False


def test_degrading_requires_at_least_four_results():
    results = [_r(False), _r(True), _r(False)]
    summary = analyse("pipe", results)
    assert summary.is_degrading is False


# ---------------------------------------------------------------------------
# format_trend()
# ---------------------------------------------------------------------------

def test_format_trend_basic():
    summary = analyse("my-pipe", [_r(True), _r(False), _r(False)])
    text = format_trend(summary)
    assert "my-pipe" in text
    assert "2/3" in text


def test_format_trend_degrading_label():
    results = [_r(True), _r(True), _r(False), _r(False), _r(False), _r(False)]
    summary = analyse("pipe", results)
    text = format_trend(summary)
    assert "DEGRADING" in text


def test_format_trend_no_degrading_label_when_stable():
    results = [_r(True)] * 6
    summary = analyse("pipe", results)
    text = format_trend(summary)
    assert "DEGRADING" not in text
