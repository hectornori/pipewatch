"""Tests for pipewatch.notifiers.payload_transformer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.payload_transformer import (
    PayloadTransformer,
    transformer_from_fn,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeResult:
    pipeline: str = "test_pipe"
    success: bool = True
    error_message: str | None = None
    tags: list[str] = field(default_factory=list)


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[object] = []

    def send(self, result: object) -> None:
        self.received.append(result)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult(pipeline="pipe_a", success=False, error_message="boom")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_transform_applied_before_forward(inner, result):
    def add_tag(r):
        r.tags.append("enriched")
        return r

    notifier = PayloadTransformer(inner=inner, transform=add_tag)
    notifier.send(result)

    assert len(inner.received) == 1
    assert "enriched" in inner.received[0].tags


def test_transform_can_replace_result(inner, result):
    replacement = _FakeResult(pipeline="replaced", success=True)

    notifier = PayloadTransformer(inner=inner, transform=lambda _: replacement)
    notifier.send(result)

    assert inner.received[0].pipeline == "replaced"


def test_fallback_on_transform_error_forwards_original(inner, result):
    def bad_transform(r):
        raise ValueError("transform exploded")

    notifier = PayloadTransformer(
        inner=inner, transform=bad_transform, _fallback_on_error=True
    )
    notifier.send(result)

    assert inner.received[0] is result


def test_no_fallback_raises_on_transform_error(inner, result):
    def bad_transform(r):
        raise RuntimeError("hard failure")

    notifier = PayloadTransformer(
        inner=inner, transform=bad_transform, _fallback_on_error=False
    )
    with pytest.raises(RuntimeError, match="hard failure"):
        notifier.send(result)

    assert inner.received == []


def test_multiple_sends_each_transformed(inner):
    results = [_FakeResult(pipeline=f"p{i}") for i in range(3)]

    def mark(r):
        r.tags.append("marked")
        return r

    notifier = PayloadTransformer(inner=inner, transform=mark)
    for r in results:
        notifier.send(r)

    assert len(inner.received) == 3
    assert all("marked" in r.tags for r in inner.received)


def test_transformer_from_fn_factory(inner, result):
    notifier = transformer_from_fn(inner, lambda r: r)
    notifier.send(result)
    assert inner.received[0] is result


def test_transformer_from_fn_fallback_default(inner, result):
    notifier = transformer_from_fn(inner, lambda r: (_ for _ in ()).throw(ValueError()))
    # Should not raise — fallback is True by default
    notifier.send(result)
    assert inner.received[0] is result


def test_transformer_satisfies_protocol():
    from pipewatch.notifiers.payload_transformer import Notifier as NotifierProto

    inner = _FakeNotifier()
    notifier = PayloadTransformer(inner=inner, transform=lambda r: r)
    assert isinstance(notifier, NotifierProto)
