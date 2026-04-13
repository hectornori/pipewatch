"""Tests for WindowNotifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import List
from unittest.mock import patch

import pytest

from pipewatch.notifiers.window_notifier import WindowNotifier


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe-a"
    success: bool = True
    error_message: str | None = None


@dataclass
class _FakeNotifier:
    calls: List = field(default_factory=list)

    def send(self, result) -> None:
        self.calls.append(result)


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult()


def _notifier(inner, start="08:00", end="20:00"):
    h_s, m_s = map(int, start.split(":"))
    h_e, m_e = map(int, end.split(":"))
    return WindowNotifier(inner=inner, start=time(h_s, m_s), end=time(h_e, m_e))


def test_send_forwards_inside_window(inner, result):
    notifier = _notifier(inner)
    with patch("pipewatch.notifiers.window_notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value.time.return_value = time(10, 0)
        notifier.send(result)
    assert len(inner.calls) == 1


def test_send_suppressed_before_window(inner, result):
    notifier = _notifier(inner)
    with patch("pipewatch.notifiers.window_notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value.time.return_value = time(6, 0)
        notifier.send(result)
    assert len(inner.calls) == 0


def test_send_suppressed_after_window(inner, result):
    notifier = _notifier(inner)
    with patch("pipewatch.notifiers.window_notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value.time.return_value = time(21, 30)
        notifier.send(result)
    assert len(inner.calls) == 0


def test_send_at_exact_start_is_included(inner, result):
    notifier = _notifier(inner)
    with patch("pipewatch.notifiers.window_notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value.time.return_value = time(8, 0)
        notifier.send(result)
    assert len(inner.calls) == 1


def test_send_at_exact_end_is_excluded(inner, result):
    notifier = _notifier(inner)
    with patch("pipewatch.notifiers.window_notifier.datetime") as mock_dt:
        mock_dt.utcnow.return_value.time.return_value = time(20, 0)
        notifier.send(result)
    assert len(inner.calls) == 0


def test_invalid_window_raises():
    with pytest.raises(ValueError, match="must be before"):
        WindowNotifier(inner=_FakeNotifier(), start=time(20, 0), end=time(8, 0))


def test_equal_start_end_raises():
    with pytest.raises(ValueError):
        WindowNotifier(inner=_FakeNotifier(), start=time(9, 0), end=time(9, 0))
