"""Tests for PriorityConfig and priority_config_from_dict."""
from __future__ import annotations

import pytest

from pipewatch.priority_config import PriorityConfig, priority_config_from_dict


def test_valid_config_creates_successfully():
    cfg = PriorityConfig(routes=[{"min_priority": 5, "notifier": "slack"}])
    assert len(cfg.routes) == 1


def test_missing_min_priority_raises():
    with pytest.raises(ValueError, match="min_priority"):
        PriorityConfig(routes=[{"notifier": "slack"}])


def test_non_integer_min_priority_raises():
    with pytest.raises(TypeError, match="integer"):
        PriorityConfig(routes=[{"min_priority": "high", "notifier": "slack"}])


def test_negative_min_priority_raises():
    with pytest.raises(ValueError, match=">= 0"):
        PriorityConfig(routes=[{"min_priority": -1, "notifier": "slack"}])


def test_missing_notifier_key_raises():
    with pytest.raises(ValueError, match="notifier"):
        PriorityConfig(routes=[{"min_priority": 0}])


def test_empty_routes_allowed():
    cfg = PriorityConfig(routes=[])
    assert cfg.routes == []


def test_default_notifier_is_none_by_default():
    cfg = PriorityConfig(routes=[])
    assert cfg.default_notifier is None


def test_from_dict_parses_routes():
    data = {
        "routes": [{"min_priority": 3, "notifier": "email"}],
        "default_notifier": "slack",
    }
    cfg = priority_config_from_dict(data)
    assert len(cfg.routes) == 1
    assert cfg.default_notifier == "slack"


def test_from_dict_empty_data():
    cfg = priority_config_from_dict({})
    assert cfg.routes == []
    assert cfg.default_notifier is None
