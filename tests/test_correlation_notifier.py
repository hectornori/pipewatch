"""Tests for CorrelationNotifier and CorrelationConfig."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.correlation_notifier import (
    CorrelationNotifier,
    CorrelationWindow,
)
from pipewatch.correlation_config import (
    CorrelationConfig,
    correlation_config_from_dict,
    wrap_with_correlation,
)


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe_a"
    success: bool = False
    error_message: str | None = "boom"


@dataclass
class _FakeNotifier:
    received: List[object] = field(default_factory=list)

    def send(self, result: object) -> None:
        self.received.append(result)


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier) -> CorrelationNotifier:
    return CorrelationNotifier(inner=inner)


# --- CorrelationWindow ---

def test_correlation_id_is_deterministic() -> None:
    w = CorrelationWindow()
    assert w.correlation_id("pipe", "err") == w.correlation_id("pipe", "err")


def test_correlation_id_differs_by_pipeline() -> None:
    w = CorrelationWindow()
    assert w.correlation_id("pipe_a", "err") != w.correlation_id("pipe_b", "err")


def test_correlation_id_differs_by_error() -> None:
    w = CorrelationWindow()
    assert w.correlation_id("pipe", "err_a") != w.correlation_id("pipe", "err_b")


def test_correlation_id_stable_with_none_error() -> None:
    w = CorrelationWindow()
    assert w.correlation_id("pipe", None) == w.correlation_id("pipe", None)


def test_group_size_increments() -> None:
    w = CorrelationWindow()
    cid = w.correlation_id("pipe", "err")
    w.register(cid, object())
    w.register(cid, object())
    assert w.group_size(cid) == 2


# --- CorrelationNotifier ---

def test_send_forwards_on_success(inner: _FakeNotifier, notifier: CorrelationNotifier) -> None:
    result = _FakeResult(success=True, error_message=None)
    notifier.send(result)
    assert len(inner.received) == 1
    assert inner.received[0] is result  # passed through unchanged


def test_send_annotates_on_failure(inner: _FakeNotifier, notifier: CorrelationNotifier) -> None:
    result = _FakeResult(success=False)
    notifier.send(result)
    assert len(inner.received) == 1
    annotated = inner.received[0]
    assert hasattr(annotated, "correlation_id")
    assert hasattr(annotated, "group_size")
    assert annotated.group_size == 1


def test_group_size_increments_across_sends(inner: _FakeNotifier, notifier: CorrelationNotifier) -> None:
    r1 = _FakeResult(pipeline_name="pipe", error_message="boom")
    r2 = _FakeResult(pipeline_name="pipe", error_message="boom")
    notifier.send(r1)
    notifier.send(r2)
    assert inner.received[0].group_size == 1
    assert inner.received[1].group_size == 2


def test_different_pipelines_get_different_ids(inner: _FakeNotifier, notifier: CorrelationNotifier) -> None:
    notifier.send(_FakeResult(pipeline_name="a", error_message="e"))
    notifier.send(_FakeResult(pipeline_name="b", error_message="e"))
    assert inner.received[0].correlation_id != inner.received[1].correlation_id


# --- CorrelationConfig ---

def test_default_config() -> None:
    cfg = CorrelationConfig()
    assert cfg.window_seconds == 60


def test_invalid_window_raises() -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        CorrelationConfig(window_seconds=0)


def test_from_dict_defaults() -> None:
    cfg = correlation_config_from_dict({})
    assert cfg.window_seconds == 60


def test_from_dict_custom() -> None:
    cfg = correlation_config_from_dict({"window_seconds": 120})
    assert cfg.window_seconds == 120


def test_wrap_with_correlation_returns_notifier() -> None:
    fake = _FakeNotifier()
    wrapped = wrap_with_correlation(fake)
    assert isinstance(wrapped, CorrelationNotifier)
