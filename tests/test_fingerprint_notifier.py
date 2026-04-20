"""Tests for FingerprintNotifier, FingerprintStore, and FingerprintConfig."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.fingerprint_notifier import (
    FingerprintNotifier,
    FingerprintStore,
    _make_fingerprint,
)
from pipewatch.fingerprint_config import (
    FingerprintConfig,
    fingerprint_config_from_dict,
    wrap_with_fingerprint,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _FakeResult:
    def __init__(self, pipeline_name="pipe", success=False, error_message="boom"):
        self.pipeline_name = pipeline_name
        self.success = success
        self.error_message = error_message


@pytest.fixture()
def store():
    return FingerprintStore(db_path=":memory:")


@pytest.fixture()
def inner():
    m = MagicMock()
    m.send = MagicMock()
    return m


@pytest.fixture()
def notifier(inner, store):
    return FingerprintNotifier(inner=inner, store=store, ttl_seconds=60.0)


@pytest.fixture()
def result():
    return _FakeResult()


# ---------------------------------------------------------------------------
# FingerprintStore
# ---------------------------------------------------------------------------


def test_not_known_before_record(store):
    assert store.is_known("abc", ttl_seconds=60) is False


def test_known_after_record(store):
    store.record("abc")
    assert store.is_known("abc", ttl_seconds=60) is True


def test_not_known_after_ttl_expires(store):
    store.record("abc")
    # Simulate record being older than TTL by querying with tiny TTL
    assert store.is_known("abc", ttl_seconds=0.0001) is False


# ---------------------------------------------------------------------------
# _make_fingerprint
# ---------------------------------------------------------------------------


def test_fingerprint_is_deterministic():
    r = _FakeResult()
    assert _make_fingerprint(r) == _make_fingerprint(r)


def test_fingerprint_differs_by_pipeline():
    a = _FakeResult(pipeline_name="a")
    b = _FakeResult(pipeline_name="b")
    assert _make_fingerprint(a) != _make_fingerprint(b)


def test_fingerprint_differs_by_error():
    a = _FakeResult(error_message="err1")
    b = _FakeResult(error_message="err2")
    assert _make_fingerprint(a) != _make_fingerprint(b)


def test_fingerprint_none_error_stable():
    r = _FakeResult(error_message=None)
    fp1 = _make_fingerprint(r)
    fp2 = _make_fingerprint(r)
    assert fp1 == fp2


# ---------------------------------------------------------------------------
# FingerprintNotifier
# ---------------------------------------------------------------------------


def test_send_forwards_first_alert(inner, notifier, result):
    notifier.send(result)
    inner.send.assert_called_once_with(result)


def test_send_suppresses_duplicate(inner, notifier, result):
    notifier.send(result)
    notifier.send(result)
    assert inner.send.call_count == 1


def test_send_forwards_different_pipeline(inner, store):
    n = FingerprintNotifier(inner=inner, store=store, ttl_seconds=60)
    n.send(_FakeResult(pipeline_name="pipe_a"))
    n.send(_FakeResult(pipeline_name="pipe_b"))
    assert inner.send.call_count == 2


def test_invalid_ttl_raises(inner, store):
    with pytest.raises(ValueError):
        FingerprintNotifier(inner=inner, store=store, ttl_seconds=0)


# ---------------------------------------------------------------------------
# FingerprintConfig
# ---------------------------------------------------------------------------


def test_default_config_creates_successfully():
    cfg = FingerprintConfig()
    assert cfg.ttl_seconds == 300.0
    assert cfg.db_path == ":memory:"


def test_invalid_ttl_config_raises():
    with pytest.raises(ValueError):
        FingerprintConfig(ttl_seconds=-1)


def test_empty_db_path_raises():
    with pytest.raises(ValueError):
        FingerprintConfig(db_path="")


def test_from_dict_defaults():
    cfg = fingerprint_config_from_dict({})
    assert cfg.ttl_seconds == 300.0


def test_from_dict_custom():
    cfg = fingerprint_config_from_dict({"ttl_seconds": 120, "db_path": "/tmp/fp.db"})
    assert cfg.ttl_seconds == 120.0
    assert cfg.db_path == "/tmp/fp.db"


def test_wrap_with_fingerprint_returns_notifier(inner):
    cfg = FingerprintConfig(ttl_seconds=60)
    wrapped = wrap_with_fingerprint(inner, cfg)
    assert isinstance(wrapped, FingerprintNotifier)
    assert wrapped.ttl_seconds == 60.0
