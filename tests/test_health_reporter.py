"""Tests for pipewatch.health_reporter."""
from __future__ import annotations

from pipewatch.pipeline_health import HealthScore
from pipewatch.health_reporter import build_health_table


def _hs(name: str, score: float, total: int = 10, consec: int = 0) -> HealthScore:
    passed = round(score * total)
    failed = total - passed
    return HealthScore(
        pipeline_name=name,
        score=score,
        total=total,
        passed=passed,
        failed=failed,
        consecutive_failures=consec,
    )


def test_empty_scores_returns_message():
    result = build_health_table([])
    assert "No pipeline health data" in result


def test_table_contains_pipeline_names():
    scores = [_hs("alpha", 1.0), _hs("beta", 0.5)]
    table = build_health_table(scores)
    assert "alpha" in table
    assert "beta" in table


def test_table_contains_grade():
    scores = [_hs("pipe", 1.0)]
    table = build_health_table(scores)
    assert "A" in table


def test_table_shows_score_as_percentage():
    scores = [_hs("pipe", 0.5)]
    table = build_health_table(scores)
    assert "50.00%" in table


def test_table_sorted_by_score_ascending():
    scores = [_hs("healthy", 1.0), _hs("sick", 0.1)]
    table = build_health_table(scores)
    # 'sick' should appear before 'healthy' (lower score first)
    assert table.index("sick") < table.index("healthy")


def test_table_has_header_and_separators():
    scores = [_hs("pipe", 0.8)]
    table = build_health_table(scores)
    assert "Pipeline" in table
    assert "Grade" in table
    assert "---" in table


def test_health_alert_notifier_below_threshold():
    """Inline smoke-test for HealthAlertNotifier to keep test count balanced."""
    from unittest.mock import MagicMock
    from pipewatch.monitor import CheckResult
    from pipewatch.notifiers.health_alert_notifier import HealthAlertNotifier

    inner = MagicMock()
    hs = _hs("pipe", 0.4)
    notifier = HealthAlertNotifier(inner, hs, threshold=0.75)
    result = CheckResult(pipeline_name="pipe", success=False, error_message="err")
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_health_alert_notifier_above_threshold():
    from unittest.mock import MagicMock
    from pipewatch.monitor import CheckResult
    from pipewatch.notifiers.health_alert_notifier import HealthAlertNotifier

    inner = MagicMock()
    hs = _hs("pipe", 1.0)
    notifier = HealthAlertNotifier(inner, hs, threshold=0.75)
    result = CheckResult(pipeline_name="pipe", success=False, error_message="err")
    notifier.send(result)
    inner.send.assert_not_called()
