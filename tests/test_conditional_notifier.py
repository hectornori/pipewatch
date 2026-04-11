"""Tests for ConditionalNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.conditional_notifier import (
    ConditionalNotifier,
    failures_only,
    pipeline_name_matches,
)


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe_a"
    success: bool = True
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[object] = []

    def send(self, result: object) -> None:
        self.received.append(result)


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def _ok() -> _FakeResult:
    return _FakeResult(pipeline_name="pipe_a", success=True)


@pytest.fixture()
def _fail() -> _FakeResult:
    return _FakeResult(pipeline_name="pipe_a", success=False, error_message="boom")


# ---------------------------------------------------------------------------
# Basic forwarding
# ---------------------------------------------------------------------------

def test_forwards_when_predicate_true(inner: _FakeNotifier, _ok: _FakeResult) -> None:
    notifier = ConditionalNotifier(inner=inner, predicate=lambda _: True)
    notifier.send(_ok)
    assert len(inner.received) == 1
    assert inner.received[0] is _ok


def test_skips_when_predicate_false(inner: _FakeNotifier, _ok: _FakeResult) -> None:
    notifier = ConditionalNotifier(inner=inner, predicate=lambda _: False)
    notifier.send(_ok)
    assert inner.received == []


def test_skip_log_label_does_not_raise(inner: _FakeNotifier, _ok: _FakeResult) -> None:
    notifier = ConditionalNotifier(
        inner=inner, predicate=lambda _: False, skip_log="test-gate"
    )
    notifier.send(_ok)  # should not raise
    assert inner.received == []


# ---------------------------------------------------------------------------
# failures_only predicate
# ---------------------------------------------------------------------------

def test_failures_only_blocks_success(inner: _FakeNotifier, _ok: _FakeResult) -> None:
    notifier = ConditionalNotifier(inner=inner, predicate=failures_only())
    notifier.send(_ok)
    assert inner.received == []


def test_failures_only_passes_failure(inner: _FakeNotifier, _fail: _FakeResult) -> None:
    notifier = ConditionalNotifier(inner=inner, predicate=failures_only())
    notifier.send(_fail)
    assert len(inner.received) == 1


# ---------------------------------------------------------------------------
# pipeline_name_matches predicate
# ---------------------------------------------------------------------------

def test_pipeline_name_matches_passes_matching(inner: _FakeNotifier) -> None:
    result = _FakeResult(pipeline_name="pipe_x")
    notifier = ConditionalNotifier(
        inner=inner, predicate=pipeline_name_matches("pipe_x", "pipe_y")
    )
    notifier.send(result)
    assert len(inner.received) == 1


def test_pipeline_name_matches_blocks_non_matching(inner: _FakeNotifier) -> None:
    result = _FakeResult(pipeline_name="pipe_z")
    notifier = ConditionalNotifier(
        inner=inner, predicate=pipeline_name_matches("pipe_x", "pipe_y")
    )
    notifier.send(result)
    assert inner.received == []


def test_pipeline_name_matches_missing_attr(inner: _FakeNotifier) -> None:
    notifier = ConditionalNotifier(
        inner=inner, predicate=pipeline_name_matches("pipe_a")
    )
    notifier.send(object())  # no pipeline_name attribute
    assert inner.received == []
