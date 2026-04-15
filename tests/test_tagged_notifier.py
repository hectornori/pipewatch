"""Tests for TaggedNotifier and TaggedNotifierConfig."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from pipewatch.notifiers.tagged_notifier import TaggedNotifier, _TaggedResult
from pipewatch.tagged_notifier_config import (
    TaggedNotifierConfig,
    tagged_notifier_config_from_dict,
    wrap_with_tags,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe-a"
    success: bool = True
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class _FakeNotifier:
    received: list[Any] = field(default_factory=list)

    def send(self, result: Any) -> None:
        self.received.append(result)


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult(tags={"existing": "yes"})


# ---------------------------------------------------------------------------
# _TaggedResult
# ---------------------------------------------------------------------------


def test_tagged_result_merges_tags() -> None:
    base = _FakeResult(tags={"a": "1"})
    wrapped = _TaggedResult(_inner=base, _extra_tags={"b": "2"})
    assert wrapped.tags == {"a": "1", "b": "2"}


def test_tagged_result_extra_tags_override_base() -> None:
    base = _FakeResult(tags={"env": "staging"})
    wrapped = _TaggedResult(_inner=base, _extra_tags={"env": "production"})
    assert wrapped.tags["env"] == "production"


def test_tagged_result_proxies_other_attrs() -> None:
    base = _FakeResult(pipeline_name="my-pipe")
    wrapped = _TaggedResult(_inner=base, _extra_tags={})
    assert wrapped.pipeline_name == "my-pipe"


# ---------------------------------------------------------------------------
# TaggedNotifier
# ---------------------------------------------------------------------------


def test_send_forwards_when_no_tags(inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier = TaggedNotifier(inner=inner, tags={})
    notifier.send(result)
    assert inner.received[0] is result


def test_send_wraps_result_with_tags(inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier = TaggedNotifier(inner=inner, tags={"team": "data"})
    notifier.send(result)
    sent = inner.received[0]
    assert sent.tags["team"] == "data"


def test_send_preserves_existing_tags(inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier = TaggedNotifier(inner=inner, tags={"new": "tag"})
    notifier.send(result)
    sent = inner.received[0]
    assert sent.tags["existing"] == "yes"
    assert sent.tags["new"] == "tag"


# ---------------------------------------------------------------------------
# TaggedNotifierConfig
# ---------------------------------------------------------------------------


def test_config_default_is_empty() -> None:
    cfg = TaggedNotifierConfig()
    assert cfg.tags == {}


def test_config_rejects_non_dict_tags() -> None:
    with pytest.raises(TypeError):
        TaggedNotifierConfig(tags="bad")  # type: ignore[arg-type]


def test_config_rejects_blank_key() -> None:
    with pytest.raises(ValueError):
        TaggedNotifierConfig(tags={"  ": "value"})


def test_from_dict_parses_tags() -> None:
    cfg = tagged_notifier_config_from_dict({"tags": {"env": "prod"}})
    assert cfg.tags == {"env": "prod"}


def test_from_dict_empty_tags() -> None:
    cfg = tagged_notifier_config_from_dict({})
    assert cfg.tags == {}


def test_wrap_with_tags_returns_tagged_notifier(inner: _FakeNotifier) -> None:
    notifier = wrap_with_tags(inner, {"tags": {"env": "prod"}})
    assert isinstance(notifier, TaggedNotifier)
    assert notifier.tags == {"env": "prod"}
