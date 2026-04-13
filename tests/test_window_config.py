"""Tests for window_config helpers."""
from __future__ import annotations

from datetime import time

import pytest

from pipewatch.window_config import WindowConfig, window_config_from_dict, wrap_with_window


def test_valid_config_creates_successfully():
    cfg = WindowConfig(start=time(8, 0), end=time(20, 0))
    assert cfg.start == time(8, 0)
    assert cfg.end == time(20, 0)
    assert cfg.tz is None


def test_invalid_start_after_end_raises():
    with pytest.raises(ValueError, match="must be before"):
        WindowConfig(start=time(20, 0), end=time(8, 0))


def test_parse_time_valid():
    assert WindowConfig._parse_time("09:30") == time(9, 30)


def test_parse_time_invalid_raises():
    with pytest.raises(ValueError, match="Invalid time string"):
        WindowConfig._parse_time("not-a-time")


def test_from_dict_minimal():
    cfg = window_config_from_dict({"start": "08:00", "end": "18:00"})
    assert cfg.start == time(8, 0)
    assert cfg.end == time(18, 0)
    assert cfg.tz is None


def test_from_dict_with_tz():
    cfg = window_config_from_dict({"start": "09:00", "end": "17:00", "tz": "Europe/London"})
    assert cfg.tz == "Europe/London"


def test_from_dict_missing_start_raises():
    with pytest.raises(KeyError, match="start"):
        window_config_from_dict({"end": "18:00"})


def test_from_dict_missing_end_raises():
    with pytest.raises(KeyError, match="end"):
        window_config_from_dict({"start": "08:00"})


def test_wrap_with_window_returns_window_notifier():
    from pipewatch.notifiers.window_notifier import WindowNotifier

    class _Fake:
        def send(self, r): pass

    wrapped = wrap_with_window(_Fake(), {"start": "08:00", "end": "20:00"})
    assert isinstance(wrapped, WindowNotifier)
    assert wrapped.start == time(8, 0)
    assert wrapped.end == time(20, 0)
