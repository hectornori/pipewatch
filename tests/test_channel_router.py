"""Tests for ChannelRouter."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from pipewatch.monitor import CheckResult
from pipewatch.notifiers.channel_router import ChannelRoute, ChannelRouter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeNotifier:
    received: List[CheckResult] = field(default_factory=list)

    def send(self, result: CheckResult) -> None:
        self.received.append(result)


def _make_result(name: str, success: bool = True) -> CheckResult:
    return CheckResult(
        pipeline_name=name,
        success=success,
        error_message=None if success else "boom",
    )


# ---------------------------------------------------------------------------
# ChannelRoute.matches
# ---------------------------------------------------------------------------

def test_route_matches_exact():
    n = _FakeNotifier()
    route = ChannelRoute(pattern="payments", notifier=n)
    assert route.matches("payments") is True


def test_route_no_match_different_name():
    n = _FakeNotifier()
    route = ChannelRoute(pattern="payments", notifier=n)
    assert route.matches("orders") is False


def test_route_glob_wildcard():
    n = _FakeNotifier()
    route = ChannelRoute(pattern="etl_*", notifier=n)
    assert route.matches("etl_orders") is True
    assert route.matches("etl_payments") is True
    assert route.matches("batch_orders") is False


# ---------------------------------------------------------------------------
# ChannelRouter.send — matching
# ---------------------------------------------------------------------------

def test_first_matching_route_receives_result():
    first = _FakeNotifier()
    second = _FakeNotifier()
    router = ChannelRouter()
    router.register("payments*", first)
    router.register("payments_v2", second)

    result = _make_result("payments_v2")
    router.send(result)

    assert len(first.received) == 1
    assert len(second.received) == 0


def test_second_route_used_when_first_does_not_match():
    first = _FakeNotifier()
    second = _FakeNotifier()
    router = ChannelRouter()
    router.register("orders*", first)
    router.register("payments*", second)

    result = _make_result("payments_daily")
    router.send(result)

    assert len(first.received) == 0
    assert len(second.received) == 1


# ---------------------------------------------------------------------------
# ChannelRouter.send — default fallback
# ---------------------------------------------------------------------------

def test_default_notifier_used_when_no_match():
    specific = _FakeNotifier()
    default = _FakeNotifier()
    router = ChannelRouter(default=default)
    router.register("orders*", specific)

    result = _make_result("payments_daily")
    router.send(result)

    assert len(specific.received) == 0
    assert len(default.received) == 1


def test_no_dispatch_when_no_match_and_no_default():
    specific = _FakeNotifier()
    router = ChannelRouter()
    router.register("orders*", specific)

    router.send(_make_result("payments_daily"))  # should not raise

    assert len(specific.received) == 0


def test_default_not_called_when_route_matches():
    specific = _FakeNotifier()
    default = _FakeNotifier()
    router = ChannelRouter(default=default)
    router.register("pay*", specific)

    router.send(_make_result("payments"))

    assert len(specific.received) == 1
    assert len(default.received) == 0


# ---------------------------------------------------------------------------
# register helper
# ---------------------------------------------------------------------------

def test_register_appends_route():
    n = _FakeNotifier()
    router = ChannelRouter()
    router.register("etl_*", n)
    assert len(router.routes) == 1
    assert router.routes[0].pattern == "etl_*"
