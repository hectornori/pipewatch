"""Tests for pipewatch.notifiers.header_notifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from pipewatch.notifiers.header_notifier import (
    HeaderNotifier,
    _HeaderedResult,
    header_notifier_from_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe-a"
    success: bool = True
    error_message: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class _FakeNotifier:
    def __init__(self) -> None:
        self.received: list[Any] = []

    def send(self, result: Any) -> None:
        self.received.append(result)


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult()


# ---------------------------------------------------------------------------
# HeaderedResult
# ---------------------------------------------------------------------------


def test_headered_result_proxies_attributes() -> None:
    base = _FakeResult(pipeline_name="my-pipe")
    hr = _HeaderedResult(_inner=base, _headers={"env": "prod"})
    assert hr.pipeline_name == "my-pipe"


def test_headered_result_merges_metadata() -> None:
    base = _FakeResult(metadata={"team": "data"})
    hr = _HeaderedResult(_inner=base, _headers={"env": "staging"})
    assert hr.metadata == {"team": "data", "env": "staging"}


def test_headered_result_headers_override_base_metadata() -> None:
    base = _FakeResult(metadata={"env": "prod"})
    hr = _HeaderedResult(_inner=base, _headers={"env": "staging"})
    assert hr.metadata["env"] == "staging"


def test_headered_result_no_base_metadata() -> None:
    base = _FakeResult()
    base.metadata = {}  # type: ignore[assignment]
    hr = _HeaderedResult(_inner=base, _headers={"x": "1"})
    assert hr.metadata == {"x": "1"}


# ---------------------------------------------------------------------------
# HeaderNotifier.send
# ---------------------------------------------------------------------------


def test_send_forwards_to_inner(inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier = HeaderNotifier(inner=inner, headers={"env": "prod"})
    notifier.send(result)
    assert len(inner.received) == 1


def test_send_wraps_result_with_headers(inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier = HeaderNotifier(inner=inner, headers={"env": "prod", "team": "infra"})
    notifier.send(result)
    forwarded = inner.received[0]
    assert isinstance(forwarded, _HeaderedResult)
    assert forwarded.metadata["env"] == "prod"
    assert forwarded.metadata["team"] == "infra"


def test_send_with_empty_headers(inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier = HeaderNotifier(inner=inner, headers={})
    notifier.send(result)
    forwarded = inner.received[0]
    assert forwarded.metadata == {}


def test_headers_snapshot_is_independent(inner: _FakeNotifier, result: _FakeResult) -> None:
    """Mutating headers after send should not affect already-sent results."""
    notifier = HeaderNotifier(inner=inner, headers={"env": "prod"})
    notifier.send(result)
    notifier.headers["env"] = "dev"  # mutate after send
    forwarded = inner.received[0]
    assert forwarded.metadata["env"] == "prod"


# ---------------------------------------------------------------------------
# HeaderNotifier.add_header
# ---------------------------------------------------------------------------


def test_add_header_sets_value(inner: _FakeNotifier) -> None:
    notifier = HeaderNotifier(inner=inner)
    notifier.add_header("region", "eu-west-1")
    assert notifier.headers["region"] == "eu-west-1"


def test_add_header_empty_key_raises(inner: _FakeNotifier) -> None:
    notifier = HeaderNotifier(inner=inner)
    with pytest.raises(ValueError, match="empty"):
        notifier.add_header("", "value")


# ---------------------------------------------------------------------------
# header_notifier_from_dict
# ---------------------------------------------------------------------------


def test_from_dict_builds_notifier(inner: _FakeNotifier) -> None:
    notifier = header_notifier_from_dict({"headers": {"env": "prod"}}, inner)
    assert isinstance(notifier, HeaderNotifier)
    assert notifier.headers == {"env": "prod"}


def test_from_dict_empty_headers(inner: _FakeNotifier) -> None:
    notifier = header_notifier_from_dict({}, inner)
    assert notifier.headers == {}


def test_from_dict_invalid_headers_type_raises(inner: _FakeNotifier) -> None:
    with pytest.raises(TypeError, match="mapping"):
        header_notifier_from_dict({"headers": "not-a-dict"}, inner)


def test_from_dict_coerces_values_to_str(inner: _FakeNotifier) -> None:
    notifier = header_notifier_from_dict({"headers": {"retry": 3}}, inner)
    assert notifier.headers["retry"] == "3"
