"""Tests for EnvAwareNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.env_aware_notifier import EnvAwareNotifier, SUPPRESSED_ENVS


@dataclass
class _FakeResult:
    pipeline_name: str
    success: bool = True
    error_message: str | None = None


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def inner() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult(pipeline_name="my_pipeline")


# ---------------------------------------------------------------------------
# suppression
# ---------------------------------------------------------------------------


def test_suppressed_in_local_env(inner: MagicMock, result: _FakeResult) -> None:
    notifier = EnvAwareNotifier(inner=inner, environment="local")
    notifier.send(result)
    inner.send.assert_not_called()


def test_suppressed_in_test_env(inner: MagicMock, result: _FakeResult) -> None:
    notifier = EnvAwareNotifier(inner=inner, environment="test")
    notifier.send(result)
    inner.send.assert_not_called()


def test_suppressed_env_case_insensitive(inner: MagicMock, result: _FakeResult) -> None:
    notifier = EnvAwareNotifier(inner=inner, environment="LOCAL")
    notifier.send(result)
    inner.send.assert_not_called()


# ---------------------------------------------------------------------------
# production — no tagging
# ---------------------------------------------------------------------------


def test_prod_env_forwards_unchanged(inner: MagicMock, result: _FakeResult) -> None:
    notifier = EnvAwareNotifier(inner=inner, environment="prod")
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_prod_env_pipeline_name_unchanged(inner: MagicMock) -> None:
    notifier = EnvAwareNotifier(inner=inner, environment="prod")
    r = _FakeResult(pipeline_name="etl_load")
    notifier.send(r)
    forwarded = inner.send.call_args[0][0]
    assert forwarded.pipeline_name == "etl_load"


# ---------------------------------------------------------------------------
# staging — tagging
# ---------------------------------------------------------------------------


def test_staging_env_tags_pipeline_name(inner: MagicMock) -> None:
    notifier = EnvAwareNotifier(inner=inner, environment="staging")
    r = _FakeResult(pipeline_name="etl_load")
    notifier.send(r)
    forwarded = inner.send.call_args[0][0]
    assert forwarded.pipeline_name == "[staging] etl_load"


def test_staging_env_tagging_disabled(inner: MagicMock) -> None:
    notifier = EnvAwareNotifier(inner=inner, environment="staging", tag_envs=False)
    r = _FakeResult(pipeline_name="etl_load")
    notifier.send(r)
    forwarded = inner.send.call_args[0][0]
    assert forwarded.pipeline_name == "etl_load"


# ---------------------------------------------------------------------------
# custom suppressed_envs
# ---------------------------------------------------------------------------


def test_custom_suppressed_env_blocks_send(inner: MagicMock, result: _FakeResult) -> None:
    notifier = EnvAwareNotifier(
        inner=inner,
        environment="dev",
        suppressed_envs=frozenset({"dev"}),
    )
    notifier.send(result)
    inner.send.assert_not_called()


def test_default_suppressed_envs_constant() -> None:
    assert "local" in SUPPRESSED_ENVS
    assert "test" in SUPPRESSED_ENVS
