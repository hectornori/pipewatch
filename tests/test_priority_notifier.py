"""Tests for PriorityNotifier and PriorityRoute."""
from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import List

from pipewatch.notifiers.priority_notifier import PriorityNotifier, PriorityRoute


@dataclass
class _FakeResult:
    pipeline: str = "pipe-a"
    success: bool = True
    priority: int = 0


class _FakeNotifier:
    def __init__(self):
        self.received: List = []

    def send(self, result) -> None:
        self.received.append(result)


@pytest.fixture()
def low():
    return _FakeNotifier()


@pytest.fixture()
def high():
    return _FakeNotifier()


@pytest.fixture()
def notifier(low, high):
    n = PriorityNotifier()
    n.register(min_priority=0, notifier=low)
    n.register(min_priority=10, notifier=high)
    return n


def test_route_matches_exact_threshold():
    route = PriorityRoute(min_priority=5, notifier=_FakeNotifier())
    assert route.matches(5) is True


def test_route_no_match_below_threshold():
    route = PriorityRoute(min_priority=5, notifier=_FakeNotifier())
    assert route.matches(4) is False


def test_low_priority_reaches_only_low_notifier(notifier, low, high):
    result = _FakeResult(priority=0)
    notifier.send(result)
    assert result in low.received
    assert result not in high.received


def test_high_priority_reaches_both_notifiers(notifier, low, high):
    result = _FakeResult(priority=10)
    notifier.send(result)
    assert result in low.received
    assert result in high.received


def test_missing_priority_attribute_defaults_to_zero(notifier, low, high):
    @dataclass
    class NoPriority:
        pipeline: str = "x"

    result = NoPriority()
    notifier.send(result)
    assert result in low.received
    assert result not in high.received


def test_default_notifier_called_when_no_route_matches():
    n = PriorityNotifier()
    default = _FakeNotifier()
    n.set_default(default)
    result = _FakeResult(priority=99)
    n.send(result)
    assert result in default.received


def test_default_notifier_not_called_when_route_matches():
    n = PriorityNotifier()
    inner = _FakeNotifier()
    default = _FakeNotifier()
    n.register(min_priority=0, notifier=inner)
    n.set_default(default)
    result = _FakeResult(priority=0)
    n.send(result)
    assert result in inner.received
    assert result not in default.received


def test_no_routes_no_default_is_silent():
    n = PriorityNotifier()
    result = _FakeResult(priority=5)
    n.send(result)  # should not raise
