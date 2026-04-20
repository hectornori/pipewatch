"""Tests for PatternNotifier."""
from __future__ import annotations

import pytest
from dataclasses import dataclass
from unittest.mock import MagicMock

from pipewatch.notifiers.pattern_notifier import (
    PatternNotifier,
    pattern_notifier_from_dict,
)


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe"
    success: bool = False
    error_message: str | None = None


@pytest.fixture()
def inner():
    m = MagicMock()
    m.send = MagicMock()
    return m


@pytest.fixture()
def notifier(inner):
    return PatternNotifier(inner=inner, patterns=[r"timeout", r"connection refused"])


@pytest.fixture()
def result():
    return _FakeResult(error_message="DB timeout after 30s")


def test_send_forwards_when_pattern_matches(notifier, inner, result):
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_send_suppresses_when_no_pattern_matches(notifier, inner):
    r = _FakeResult(error_message="disk full")
    notifier.send(r)
    inner.send.assert_not_called()


def test_send_suppresses_when_error_is_none(notifier, inner):
    r = _FakeResult(error_message=None)
    notifier.send(r)
    inner.send.assert_not_called()


def test_send_suppresses_when_result_has_no_error_attr(notifier, inner):
    notifier.send(object())
    inner.send.assert_not_called()


def test_invert_suppresses_when_pattern_matches(inner):
    n = PatternNotifier(inner=inner, patterns=[r"timeout"], invert=True)
    r = _FakeResult(error_message="timeout error")
    n.send(r)
    inner.send.assert_not_called()


def test_invert_forwards_when_pattern_does_not_match(inner):
    n = PatternNotifier(inner=inner, patterns=[r"timeout"], invert=True)
    r = _FakeResult(error_message="disk full")
    n.send(r)
    inner.send.assert_called_once_with(r)


def test_second_pattern_also_triggers_forward(notifier, inner):
    r = _FakeResult(error_message="connection refused by host")
    notifier.send(r)
    inner.send.assert_called_once_with(r)


def test_empty_patterns_raises():
    with pytest.raises(ValueError, match="At least one pattern"):
        PatternNotifier(inner=MagicMock(), patterns=[])


def test_from_dict_creates_notifier(inner):
    n = pattern_notifier_from_dict({"patterns": [r"error"]}, inner)
    assert isinstance(n, PatternNotifier)
    assert n.invert is False


def test_from_dict_invert_flag(inner):
    n = pattern_notifier_from_dict({"patterns": [r"error"], "invert": True}, inner)
    assert n.invert is True


def test_from_dict_missing_patterns_raises(inner):
    with pytest.raises(ValueError, match="patterns"):
        pattern_notifier_from_dict({}, inner)


def test_from_dict_empty_patterns_raises(inner):
    with pytest.raises(ValueError):
        pattern_notifier_from_dict({"patterns": []}, inner)
