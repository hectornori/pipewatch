"""Tests for SamplingNotifier."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.sampling_notifier import SamplingNotifier


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe_a"
    success: bool = True
    error_message: str | None = None


@pytest.fixture()
def inner() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult(pipeline_name="pipe_a", success=False, error_message="boom")


def test_rate_one_always_forwards(inner: MagicMock, result: _FakeResult) -> None:
    notifier = SamplingNotifier(inner=inner, sample_rate=1.0, seed=42)
    for _ in range(10):
        notifier.send(result)
    assert inner.send.call_count == 10


def test_rate_zero_never_forwards(inner: MagicMock, result: _FakeResult) -> None:
    notifier = SamplingNotifier(inner=inner, sample_rate=0.0, seed=42)
    for _ in range(10):
        notifier.send(result)
    inner.send.assert_not_called()


def test_partial_rate_forwards_some(inner: MagicMock, result: _FakeResult) -> None:
    notifier = SamplingNotifier(inner=inner, sample_rate=0.5, seed=0)
    for _ in range(200):
        notifier.send(result)
    count = inner.send.call_count
    # With seed=0 and 200 trials at 50% we expect roughly 100 ± 30.
    assert 60 < count < 140


def test_seed_produces_deterministic_results(result: _FakeResult) -> None:
    inner_a: MagicMock = MagicMock()
    inner_b: MagicMock = MagicMock()
    for inner, seed in [(inner_a, 7), (inner_b, 7)]:
        notifier = SamplingNotifier(inner=inner, sample_rate=0.5, seed=seed)
        for _ in range(50):
            notifier.send(result)
    assert inner_a.send.call_count == inner_b.send.call_count


def test_invalid_rate_below_zero(inner: MagicMock) -> None:
    with pytest.raises(ValueError, match="sample_rate"):
        SamplingNotifier(inner=inner, sample_rate=-0.1)


def test_invalid_rate_above_one(inner: MagicMock) -> None:
    with pytest.raises(ValueError, match="sample_rate"):
        SamplingNotifier(inner=inner, sample_rate=1.1)


def test_boundary_rate_zero_is_valid(inner: MagicMock, result: _FakeResult) -> None:
    notifier = SamplingNotifier(inner=inner, sample_rate=0.0)
    notifier.send(result)
    inner.send.assert_not_called()


def test_boundary_rate_one_is_valid(inner: MagicMock, result: _FakeResult) -> None:
    notifier = SamplingNotifier(inner=inner, sample_rate=1.0)
    notifier.send(result)
    inner.send.assert_called_once_with(result)
