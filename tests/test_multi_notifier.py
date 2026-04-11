"""Tests for MultiNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock, call

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.notifiers.multi_notifier import MultiNotifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeResult:
    pipeline_name: str = "pipe"
    success: bool = True
    error_message: str | None = None


@dataclass
class _BrokenNotifier:
    """Always raises on send."""
    calls: list = field(default_factory=list)

    def send(self, result) -> None:
        self.calls.append(result)
        raise RuntimeError("boom")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult()


@pytest.fixture()
def multi() -> MultiNotifier:
    return MultiNotifier()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_send_to_single_notifier(multi, result):
    inner = MagicMock()
    multi.register(inner)
    multi.send(result)
    inner.send.assert_called_once_with(result)


def test_send_to_multiple_notifiers(multi, result):
    a, b, c = MagicMock(), MagicMock(), MagicMock()
    for n in (a, b, c):
        multi.register(n)
    multi.send(result)
    for n in (a, b, c):
        n.send.assert_called_once_with(result)


def test_send_with_no_notifiers_does_not_raise(multi, result):
    # Should be a no-op
    multi.send(result)


def test_broken_notifier_does_not_block_others(multi, result):
    broken = _BrokenNotifier()
    good = MagicMock()
    multi.register(broken)
    multi.register(good)
    # Must not raise
    multi.send(result)
    good.send.assert_called_once_with(result)
    assert broken.calls == [result]


def test_all_broken_notifiers_do_not_raise(multi, result):
    for _ in range(3):
        multi.register(_BrokenNotifier())
    # Should swallow all errors
    multi.send(result)


def test_register_invalid_notifier_raises(multi):
    with pytest.raises(TypeError):
        multi.register(object())


def test_register_adds_to_list(multi):
    a, b = MagicMock(), MagicMock()
    multi.register(a)
    multi.register(b)
    assert multi.notifiers == [a, b]


def test_send_order_matches_registration(multi, result):
    order: list[int] = []

    class _Ordered:
        def __init__(self, idx: int):
            self._idx = idx

        def send(self, _result) -> None:
            order.append(self._idx)

    for i in range(4):
        multi.register(_Ordered(i))

    multi.send(result)
    assert order == [0, 1, 2, 3]
