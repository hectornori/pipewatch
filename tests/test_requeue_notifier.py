"""Tests for RequeueNotifier, RequeueStore, and RequeueConfig."""
from __future__ import annotations

import pytest

from pipewatch.notifiers.requeue_notifier import RequeueNotifier, RequeueStore
from pipewatch.requeue_config import RequeueConfig, requeue_config_from_dict, wrap_with_requeue


@pytest.fixture
class _FakeResult:
    def __init__(self, pipeline_name="pipe1", error_message=None, success=True):
        self.pipeline_name = pipeline_name
        self.error_message = error_message
        self.success = success


@pytest.fixture
def store(tmp_path):
    return RequeueStore(db_path=str(tmp_path / "requeue.db"))


@pytest.fixture
def inner():
    class _FakeNotifier:
        def __init__(self):
            self.received = []
            self.raise_on_next = False

        def send(self, result):
            if self.raise_on_next:
                self.raise_on_next = False
                raise RuntimeError("send failed")
            self.received.append(result)

    return _FakeNotifier()


@pytest.fixture
def notifier(inner, store):
    return RequeueNotifier(inner=inner, store=store)


@pytest.fixture
def result():
    class R:
        pipeline_name = "pipe1"
        error_message = "boom"
        success = False
    return R()


def test_send_forwards_on_success(notifier, inner, result):
    notifier.send(result)
    assert len(inner.received) == 1


def test_send_enqueues_on_failure(notifier, inner, store, result):
    inner.raise_on_next = True
    notifier.send(result)
    assert store.count() == 1


def test_send_does_not_raise_on_inner_failure(notifier, inner, result):
    inner.raise_on_next = True
    notifier.send(result)  # should not raise


def test_flush_retries_queued_entry(notifier, inner, store, result):
    inner.raise_on_next = True
    notifier.send(result)
    assert store.count() == 1

    def factory(pipeline, error):
        class R:
            pipeline_name = pipeline
            error_message = error
        return R()

    success = notifier.flush(factory)
    assert success == 1
    assert store.count() == 0


def test_flush_leaves_entry_on_factory_failure(notifier, inner, store, result):
    inner.raise_on_next = True
    notifier.send(result)

    def bad_factory(pipeline, error):
        raise ValueError("factory error")

    success = notifier.flush(bad_factory)
    assert success == 0
    assert store.count() == 1


def test_default_config_creates_successfully():
    cfg = RequeueConfig()
    assert cfg.flush_limit == 10


def test_invalid_db_path_raises():
    with pytest.raises(ValueError, match="db_path"):
        RequeueConfig(db_path="")


def test_invalid_flush_limit_raises():
    with pytest.raises(ValueError, match="flush_limit"):
        RequeueConfig(flush_limit=0)


def test_from_dict_defaults():
    cfg = requeue_config_from_dict({})
    assert cfg.db_path == "pipewatch_requeue.db"
    assert cfg.flush_limit == 10


def test_wrap_with_requeue_returns_notifier(tmp_path, inner):
    cfg = RequeueConfig(db_path=str(tmp_path / "rq.db"))
    n = wrap_with_requeue(inner, cfg)
    assert isinstance(n, RequeueNotifier)
