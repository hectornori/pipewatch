"""Tests for pipewatch.label_router."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.label_router import LabelRoute, LabelRouter
from pipewatch.monitor import CheckResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(tags=None, success=True):
    pipeline = MagicMock()
    pipeline.tags = tags or []
    return CheckResult(pipeline=pipeline, success=success, error_message=None)


# ---------------------------------------------------------------------------
# LabelRoute
# ---------------------------------------------------------------------------

def test_label_route_matches_when_tag_present():
    notifier = MagicMock()
    route = LabelRoute(label="critical", notifier=notifier)
    result = _make_result(tags=["critical", "finance"])
    assert route.matches(result) is True


def test_label_route_no_match_when_tag_absent():
    notifier = MagicMock()
    route = LabelRoute(label="critical", notifier=notifier)
    result = _make_result(tags=["finance"])
    assert route.matches(result) is False


def test_label_route_no_match_empty_tags():
    notifier = MagicMock()
    route = LabelRoute(label="critical", notifier=notifier)
    result = _make_result(tags=[])
    assert route.matches(result) is False


def test_label_route_handles_missing_tags_attribute():
    notifier = MagicMock()
    route = LabelRoute(label="critical", notifier=notifier)
    result = _make_result()
    result.pipeline.tags = None  # simulate absent tags
    assert route.matches(result) is False


# ---------------------------------------------------------------------------
# LabelRouter.dispatch
# ---------------------------------------------------------------------------

def test_dispatch_sends_to_matching_notifier():
    n1 = MagicMock()
    router = LabelRouter()
    router.add_route("critical", n1)
    result = _make_result(tags=["critical"])
    router.dispatch(result)
    n1.send.assert_called_once_with(result)


def test_dispatch_sends_to_multiple_matching_notifiers():
    n1, n2 = MagicMock(), MagicMock()
    router = LabelRouter()
    router.add_route("critical", n1)
    router.add_route("finance", n2)
    result = _make_result(tags=["critical", "finance"])
    router.dispatch(result)
    n1.send.assert_called_once_with(result)
    n2.send.assert_called_once_with(result)


def test_dispatch_uses_default_when_no_match():
    default = MagicMock()
    n1 = MagicMock()
    router = LabelRouter(default=default)
    router.add_route("critical", n1)
    result = _make_result(tags=["finance"])
    router.dispatch(result)
    default.send.assert_called_once_with(result)
    n1.send.assert_not_called()


def test_dispatch_no_default_and_no_match_is_silent():
    n1 = MagicMock()
    router = LabelRouter()
    router.add_route("critical", n1)
    result = _make_result(tags=["finance"])
    router.dispatch(result)  # should not raise
    n1.send.assert_not_called()


def test_default_not_called_when_route_matches():
    default = MagicMock()
    n1 = MagicMock()
    router = LabelRouter(default=default)
    router.add_route("critical", n1)
    result = _make_result(tags=["critical"])
    router.dispatch(result)
    default.send.assert_not_called()


# ---------------------------------------------------------------------------
# LabelRouter.dispatch_all
# ---------------------------------------------------------------------------

def test_dispatch_all_iterates_all_results():
    n1 = MagicMock()
    router = LabelRouter()
    router.add_route("critical", n1)
    results = [_make_result(tags=["critical"]) for _ in range(3)]
    router.dispatch_all(results)
    assert n1.send.call_count == 3
