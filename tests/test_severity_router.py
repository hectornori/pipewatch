"""Tests for pipewatch.notifiers.severity_router."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pytest

from pipewatch.notifiers.severity_router import SeverityRoute, SeverityRouter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeResult:
    pipeline: str = "pipe"
    severity: str | None = None


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: List[object] = []

    def send(self, result: object) -> None:
        self.received.append(result)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def critical_notifier() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def default_notifier() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def router(critical_notifier: _FakeNotifier) -> SeverityRouter:
    r = SeverityRouter()
    r.register("critical", critical_notifier)
    return r


# ---------------------------------------------------------------------------
# SeverityRoute unit tests
# ---------------------------------------------------------------------------

def test_severity_route_matches_correct_severity() -> None:
    notifier = _FakeNotifier()
    route = SeverityRoute(severity="high", notifier=notifier)
    assert route.matches(_FakeResult(severity="high")) is True


def test_severity_route_no_match_different_severity() -> None:
    notifier = _FakeNotifier()
    route = SeverityRoute(severity="high", notifier=notifier)
    assert route.matches(_FakeResult(severity="low")) is False


def test_severity_route_no_match_when_severity_missing() -> None:
    notifier = _FakeNotifier()
    route = SeverityRoute(severity="medium", notifier=notifier)
    assert route.matches(object()) is False


def test_severity_route_invalid_level_raises() -> None:
    with pytest.raises(ValueError, match="Invalid severity"):
        SeverityRoute(severity="urgent", notifier=_FakeNotifier())


# ---------------------------------------------------------------------------
# SeverityRouter tests
# ---------------------------------------------------------------------------

def test_send_dispatches_to_matching_route(
    router: SeverityRouter, critical_notifier: _FakeNotifier
) -> None:
    result = _FakeResult(severity="critical")
    router.send(result)
    assert critical_notifier.received == [result]


def test_send_uses_default_when_no_route_matches(
    router: SeverityRouter, default_notifier: _FakeNotifier
) -> None:
    router.default = default_notifier
    result = _FakeResult(severity="low")
    router.send(result)
    assert default_notifier.received == [result]


def test_send_silent_drop_when_no_match_and_no_default(
    router: SeverityRouter, critical_notifier: _FakeNotifier
) -> None:
    router.send(_FakeResult(severity="medium"))
    assert critical_notifier.received == []


def test_first_matching_route_wins() -> None:
    n1, n2 = _FakeNotifier(), _FakeNotifier()
    r = SeverityRouter()
    r.register("high", n1)
    r.register("high", n2)
    r.send(_FakeResult(severity="high"))
    assert len(n1.received) == 1
    assert len(n2.received) == 0


def test_register_all_valid_severities() -> None:
    r = SeverityRouter()
    for level in ("critical", "high", "medium", "low"):
        r.register(level, _FakeNotifier())
    assert len(r.routes) == 4
