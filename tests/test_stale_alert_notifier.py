"""Tests for StaleAlertNotifier and StaleAlertConfig."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.stale_alert_notifier import StaleAlertNotifier
from pipewatch.stale_alert_config import (
    StaleAlertConfig,
    stale_alert_config_from_dict,
    wrap_with_stale_alert,
)
from pipewatch.stale_detector import StalePipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool = True


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[object] = []

    def send(self, result: object) -> None:
        self.received.append(result)


def _detector(stale: bool) -> MagicMock:
    """Return a mock StaleDetector that always reports *stale* state."""
    det = MagicMock()
    det.check.return_value = (
        StalePipeline(pipeline_name="p", reason="no recent success")
        if stale
        else None
    )
    return det


# ---------------------------------------------------------------------------
# StaleAlertNotifier tests
# ---------------------------------------------------------------------------

def test_send_forwards_to_inner_when_not_stale():
    inner = _FakeNotifier()
    stale_n = _FakeNotifier()
    notifier = StaleAlertNotifier(
        inner=inner, stale_notifier=stale_n, detector=_detector(False)
    )
    result = _FakeResult(pipeline_name="pipe_a")
    notifier.send(result)

    assert inner.received == [result]
    assert stale_n.received == []


def test_send_forwards_to_stale_notifier_only_when_stale_only_true():
    inner = _FakeNotifier()
    stale_n = _FakeNotifier()
    notifier = StaleAlertNotifier(
        inner=inner, stale_notifier=stale_n, detector=_detector(True), stale_only=True
    )
    result = _FakeResult(pipeline_name="pipe_b")
    notifier.send(result)

    assert stale_n.received == [result]
    assert inner.received == []


def test_send_forwards_to_both_when_stale_only_false():
    inner = _FakeNotifier()
    stale_n = _FakeNotifier()
    notifier = StaleAlertNotifier(
        inner=inner, stale_notifier=stale_n, detector=_detector(True), stale_only=False
    )
    result = _FakeResult(pipeline_name="pipe_c")
    notifier.send(result)

    assert stale_n.received == [result]
    assert inner.received == [result]


def test_send_handles_result_without_pipeline_name():
    """Results without pipeline_name attribute should not raise."""
    inner = _FakeNotifier()
    stale_n = _FakeNotifier()
    det = _detector(False)
    notifier = StaleAlertNotifier(inner=inner, stale_notifier=stale_n, detector=det)
    notifier.send(object())  # no pipeline_name attribute
    assert inner.received  # forwarded to inner


# ---------------------------------------------------------------------------
# StaleAlertConfig tests
# ---------------------------------------------------------------------------

def test_default_config_creates_successfully():
    cfg = StaleAlertConfig()
    assert cfg.stale_threshold_minutes == 60
    assert cfg.db_path == "pipewatch.db"
    assert cfg.stale_only is True


def test_zero_threshold_raises():
    with pytest.raises(ValueError, match="stale_threshold_minutes"):
        StaleAlertConfig(stale_threshold_minutes=0)


def test_negative_threshold_raises():
    with pytest.raises(ValueError, match="stale_threshold_minutes"):
        StaleAlertConfig(stale_threshold_minutes=-5)


def test_empty_db_path_raises():
    with pytest.raises(ValueError, match="db_path"):
        StaleAlertConfig(db_path="")


def test_from_dict_defaults():
    cfg = stale_alert_config_from_dict({})
    assert cfg.stale_threshold_minutes == 60
    assert cfg.db_path == "pipewatch.db"
    assert cfg.stale_only is True


def test_from_dict_custom_values():
    cfg = stale_alert_config_from_dict(
        {"stale_threshold_minutes": 120, "db_path": "/tmp/pw.db", "stale_only": False}
    )
    assert cfg.stale_threshold_minutes == 120
    assert cfg.db_path == "/tmp/pw.db"
    assert cfg.stale_only is False
