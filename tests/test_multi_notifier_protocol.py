"""Verify that MultiNotifier itself satisfies the Notifier protocol and
can be nested inside another MultiNotifier (composition).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.notifiers.multi_notifier import MultiNotifier, Notifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeResult:
    pipeline_name = "pipe"
    success = False
    error_message = "oops"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_multi_notifier_satisfies_protocol():
    """MultiNotifier must itself be a Notifier so it can be composed."""
    assert isinstance(MultiNotifier(), Notifier)


def test_nested_multi_notifiers(caplog):
    """A MultiNotifier can be registered inside another MultiNotifier."""
    inner_leaf = MagicMock()

    inner = MultiNotifier()
    inner.register(inner_leaf)

    outer = MultiNotifier()
    outer.register(inner)  # nesting

    result = _FakeResult()
    outer.send(result)

    inner_leaf.send.assert_called_once_with(result)


def test_partial_failure_logged(caplog):
    """A failing notifier should produce an ERROR log entry."""
    import logging

    class _Boom:
        def send(self, _r) -> None:
            raise ValueError("deliberate failure")

    multi = MultiNotifier()
    multi.register(_Boom())

    with caplog.at_level(logging.ERROR, logger="pipewatch.notifiers.multi_notifier"):
        multi.send(_FakeResult())

    assert any("deliberate failure" in r.message for r in caplog.records)


def test_register_another_multi_notifier_is_valid():
    """Registering a MultiNotifier inside another must not raise TypeError."""
    outer = MultiNotifier()
    inner = MultiNotifier()
    # Should not raise
    outer.register(inner)
    assert inner in outer.notifiers
