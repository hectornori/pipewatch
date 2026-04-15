"""Tests for FanOutNotifier."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.notifiers.fan_out_notifier import FanOutNotifier


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe"
    success: bool = True
    error_message: str | None = None


class _FakeNotifier:
    def __init__(self):
        self.received: list = []
        self.lock = threading.Lock()

    def send(self, result) -> None:
        with self.lock:
            self.received.append(result)


class _BrokenNotifier:
    def send(self, result) -> None:
        raise RuntimeError("boom")


@pytest.fixture
def result():
    return _FakeResult()


def test_send_reaches_all_notifiers(result):
    a, b, c = _FakeNotifier(), _FakeNotifier(), _FakeNotifier()
    fan = FanOutNotifier(notifiers=[a, b, c])
    fan.send(result)
    assert len(a.received) == 1
    assert len(b.received) == 1
    assert len(c.received) == 1


def test_send_no_notifiers_does_not_raise(result):
    fan = FanOutNotifier()
    fan.send(result)  # should complete silently


def test_register_adds_notifier(result):
    fan = FanOutNotifier()
    notifier = _FakeNotifier()
    fan.register(notifier)
    fan.send(result)
    assert len(notifier.received) == 1


def test_failed_notifier_does_not_block_others(result):
    good = _FakeNotifier()
    fan = FanOutNotifier(notifiers=[_BrokenNotifier(), good])
    fan.send(result)  # should not raise
    assert len(good.received) == 1


def test_raise_on_all_failed_when_flag_set(result):
    fan = FanOutNotifier(
        notifiers=[_BrokenNotifier(), _BrokenNotifier()],
        raise_on_all_failed=True,
    )
    with pytest.raises(RuntimeError, match="All 2 notifiers failed"):
        fan.send(result)


def test_raise_on_all_failed_not_raised_when_one_succeeds(result):
    good = _FakeNotifier()
    fan = FanOutNotifier(
        notifiers=[_BrokenNotifier(), good],
        raise_on_all_failed=True,
    )
    fan.send(result)  # partial failure — should NOT raise
    assert len(good.received) == 1


def test_result_passed_correctly(result):
    notifier = _FakeNotifier()
    fan = FanOutNotifier(notifiers=[notifier])
    fan.send(result)
    assert notifier.received[0] is result


def test_max_workers_respected(result):
    """Smoke-test: fan-out completes with max_workers=1 (serial fallback)."""
    notifiers = [_FakeNotifier() for _ in range(5)]
    fan = FanOutNotifier(notifiers=notifiers, max_workers=1)
    fan.send(result)
    assert all(len(n.received) == 1 for n in notifiers)
