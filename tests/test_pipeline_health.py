"""Tests for pipewatch.pipeline_health."""
from __future__ import annotations

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.pipeline_health import HealthScore, compute_health, compute_all_health


def _r(success: bool, name: str = "pipe") -> CheckResult:
    return CheckResult(
        pipeline_name=name,
        success=success,
        error_message=None if success else "boom",
    )


# ---------------------------------------------------------------------------
# compute_health
# ---------------------------------------------------------------------------

def test_empty_results_returns_perfect_score():
    hs = compute_health("pipe", [])
    assert hs.score == 1.0
    assert hs.total == 0
    assert hs.grade == "A"


def test_all_passing():
    hs = compute_health("pipe", [_r(True)] * 5)
    assert hs.score == 1.0
    assert hs.passed == 5
    assert hs.failed == 0
    assert hs.consecutive_failures == 0
    assert hs.grade == "A"
    assert hs.is_healthy is True


def test_all_failing():
    hs = compute_health("pipe", [_r(False)] * 4)
    assert hs.score == 0.0
    assert hs.failed == 4
    assert hs.consecutive_failures == 4
    assert hs.grade == "F"
    assert hs.is_healthy is False


def test_mixed_results():
    results = [_r(True), _r(True), _r(False), _r(True), _r(False), _r(False)]
    hs = compute_health("pipe", results)
    assert hs.total == 6
    assert hs.passed == 3
    assert hs.failed == 3
    assert pytest.approx(hs.score, abs=1e-4) == 0.5
    assert hs.grade == "C"


def test_consecutive_failures_only_trailing():
    results = [_r(False), _r(False), _r(True), _r(False), _r(False)]
    hs = compute_health("pipe", results)
    assert hs.consecutive_failures == 2


def test_grade_boundaries():
    assert HealthScore("p", 0.9, 10, 9, 1, 0).grade == "A"
    assert HealthScore("p", 0.75, 4, 3, 1, 0).grade == "B"
    assert HealthScore("p", 0.5, 2, 1, 1, 0).grade == "C"
    assert HealthScore("p", 0.25, 4, 1, 3, 0).grade == "D"
    assert HealthScore("p", 0.1, 10, 1, 9, 0).grade == "F"


# ---------------------------------------------------------------------------
# compute_all_health
# ---------------------------------------------------------------------------

def test_compute_all_health_multiple_pipelines():
    mapping = {
        "alpha": [_r(True, "alpha")] * 3,
        "beta": [_r(False, "beta")] * 3,
    }
    scores = compute_all_health(mapping)
    by_name = {s.pipeline_name: s for s in scores}
    assert by_name["alpha"].score == 1.0
    assert by_name["beta"].score == 0.0


def test_compute_all_health_empty_mapping():
    assert compute_all_health({}) == []
