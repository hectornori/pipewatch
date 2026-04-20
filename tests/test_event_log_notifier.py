"""Tests for EventLogNotifier and EventLogStore."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from pipewatch.notifiers.event_log_notifier import EventLogNotifier, EventLogStore
from pipewatch.event_log_config import EventLogConfig, event_log_config_from_dict, wrap_with_event_log


@dataclass_fixture = None  # removed; use plain fixtures below


class _FakeResult:
    def __init__(self, pipeline_name: str, success: bool, error_message: str | None = None):
        self.pipeline_name = pipeline_name
        self.success = success
        self.error_message = error_message


@pytest.fixture
def store(tmp_path):
    return EventLogStore(db_path=str(tmp_path / "events.db"))


@pytest.fixture
def inner():
    m = MagicMock()
    m.send = MagicMock()
    return m


@pytest.fixture
def notifier(inner, store):
    return EventLogNotifier(inner=inner, store=store)


@pytest.fixture
def ok_result():
    return _FakeResult("pipeline_a", success=True)


@pytest.fixture
def fail_result():
    return _FakeResult("pipeline_a", success=False, error_message="timeout")


def test_count_zero_before_any_send(store):
    assert store.count("pipeline_a") == 0


def test_get_recent_empty_before_any_send(store):
    assert store.get_recent("pipeline_a") == []


def test_send_forwards_to_inner(notifier, inner, ok_result):
    notifier.send(ok_result)
    inner.send.assert_called_once_with(ok_result)


def test_send_records_success_event(notifier, store, ok_result):
    notifier.send(ok_result)
    entries = store.get_recent("pipeline_a")
    assert len(entries) == 1
    assert entries[0].success is True
    assert entries[0].error_message is None


def test_send_records_failure_event(notifier, store, fail_result):
    notifier.send(fail_result)
    entries = store.get_recent("pipeline_a")
    assert len(entries) == 1
    assert entries[0].success is False
    assert entries[0].error_message == "timeout"


def test_count_increments_per_send(notifier, store, ok_result, fail_result):
    notifier.send(ok_result)
    notifier.send(fail_result)
    assert store.count("pipeline_a") == 2


def test_seq_is_monotonically_increasing(store):
    seq1 = store.append("p", True, None)
    seq2 = store.append("p", False, "err")
    assert seq2 > seq1


def test_get_recent_isolated_per_pipeline(store):
    store.append("alpha", True, None)
    store.append("beta", False, "oops")
    assert store.count("alpha") == 1
    assert store.count("beta") == 1


def test_event_log_config_default():
    cfg = EventLogConfig()
    assert cfg.db_path == "pipewatch_events.db"


def test_event_log_config_empty_db_path_raises():
    with pytest.raises(ValueError, match="db_path"):
        EventLogConfig(db_path="")


def test_event_log_config_from_dict_defaults():
    cfg = event_log_config_from_dict({})
    assert cfg.db_path == "pipewatch_events.db"


def test_event_log_config_from_dict_custom(tmp_path):
    cfg = event_log_config_from_dict({"db_path": str(tmp_path / "custom.db")})
    assert "custom.db" in cfg.db_path


def test_wrap_with_event_log_returns_notifier(inner, tmp_path):
    wrapped = wrap_with_event_log(inner, {"db_path": str(tmp_path / "w.db")})
    assert isinstance(wrapped, EventLogNotifier)


def test_wrap_with_event_log_no_config(inner):
    wrapped = wrap_with_event_log(inner)
    assert isinstance(wrapped, EventLogNotifier)
