"""Tests for archive_reporter.build_archive_table."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from pipewatch.notifiers.archive_notifier import ArchiveStore
from pipewatch.archive_reporter import build_archive_table


@dataclass
class _R:
    pipeline_name: str
    success: bool
    error_message: str | None = None


@pytest.fixture
def store():
    s = ArchiveStore(db_path=":memory:")
    s.save(_R("pipe_a", False, "connection refused"))
    s.save(_R("pipe_a", True))
    return s


def test_empty_store_returns_message():
    s = ArchiveStore(db_path=":memory:")
    assert "No archived records" in build_archive_table(s, "missing")


def test_table_contains_pipeline_name(store):
    table = build_archive_table(store, "pipe_a")
    assert "pipe_a" in table


def test_table_shows_fail_status(store):
    table = build_archive_table(store, "pipe_a")
    assert "FAIL" in table


def test_table_shows_ok_status(store):
    table = build_archive_table(store, "pipe_a")
    assert "OK" in table


def test_table_shows_error_message(store):
    table = build_archive_table(store, "pipe_a")
    assert "connection refused" in table


def test_table_has_header(store):
    table = build_archive_table(store, "pipe_a")
    assert "PIPELINE" in table
    assert "STATUS" in table
    assert "ARCHIVED AT" in table
