"""Tests for PresendHookNotifier."""
from __future__ import annotations

import pytest

from pipewatch.notifiers.presend_hook_notifier import PresendHookNotifier


class _FakeResult:
    def __init__(self, name: str = "pipe", success: bool = True):
        self.pipeline_name = name
        self.success = success
        self.tags: dict = {}


class _FakeNotifier:
    def __init__(self):
        self.received = []

    def send(self, result) -> None:
        self.received.append(result)


@pytest.fixture
def inner():
    return _FakeNotifier()


@pytest.fixture
def result():
    return _FakeResult()


def test_hook_receives_result_and_forwards(inner, result):
    seen = []

    def hook(r):
        seen.append(r)
        return None  # do not replace

    notifier = PresendHookNotifier(inner=inner, hook=hook)
    notifier.send(result)

    assert seen == [result]
    assert inner.received == [result]


def test_hook_can_replace_result(inner, result):
    replacement = _FakeResult(name="replaced")

    def hook(r):
        return replacement

    notifier = PresendHookNotifier(inner=inner, hook=hook)
    notifier.send(result)

    assert inner.received == [replacement]


def test_hook_exception_aborts_send(inner, result):
    def boom(r):
        raise RuntimeError("hook failed")

    notifier = PresendHookNotifier(inner=inner, hook=boom)
    with pytest.raises(RuntimeError, match="hook failed"):
        notifier.send(result)

    assert inner.received == []


def test_multiple_hooks_applied_in_order(inner):
    log = []

    def hook_a(r):
        log.append("a")
        return None

    def hook_b(r):
        log.append("b")
        return None

    result = _FakeResult()
    notifier = PresendHookNotifier(inner=inner, hook=hook_a)
    notifier.register_hook(hook_b)
    notifier.send(result)

    assert log == ["a", "b"]
    assert inner.received == [result]


def test_register_hook_chains_replacement(inner):
    r1 = _FakeResult(name="first")
    r2 = _FakeResult(name="second")
    r3 = _FakeResult(name="third")

    notifier = PresendHookNotifier(inner=inner, hook=lambda r: r2)
    notifier.register_hook(lambda r: r3)
    notifier.send(r1)

    assert inner.received == [r3]
