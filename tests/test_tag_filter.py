"""Tests for pipewatch.tag_filter."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pipewatch.tag_filter import TagFilter, filter_from_tags


def _make_pipeline(name: str, tags=None):
    p = MagicMock()
    p.name = name
    p.tags = tags
    return p


@pytest.fixture()
def pipelines():
    return [
        _make_pipeline("alpha", ["critical", "finance"]),
        _make_pipeline("beta", ["finance"]),
        _make_pipeline("gamma", ["critical"]),
        _make_pipeline("delta", []),
        _make_pipeline("epsilon", None),
    ]


def test_empty_filter_matches_all(pipelines):
    f = TagFilter()
    assert f.apply(pipelines) == pipelines


def test_single_tag_filter(pipelines):
    f = TagFilter(required_tags=["critical"])
    result = f.apply(pipelines)
    names = [p.name for p in result]
    assert names == ["alpha", "gamma"]


def test_multi_tag_filter_requires_all(pipelines):
    f = TagFilter(required_tags=["critical", "finance"])
    result = f.apply(pipelines)
    assert len(result) == 1
    assert result[0].name == "alpha"


def test_no_match_returns_empty(pipelines):
    f = TagFilter(required_tags=["nonexistent"])
    assert f.apply(pipelines) == []


def test_matches_pipeline_with_none_tags():
    p = _make_pipeline("x", None)
    f = TagFilter(required_tags=["critical"])
    assert f.matches(p) is False


def test_matches_pipeline_with_empty_tags():
    p = _make_pipeline("x", [])
    f = TagFilter(required_tags=["critical"])
    assert f.matches(p) is False


def test_filter_from_tags_none():
    f = filter_from_tags(None)
    assert f.required_tags == []


def test_filter_from_tags_empty_list():
    f = filter_from_tags([])
    assert f.required_tags == []


def test_filter_from_tags_with_values():
    f = filter_from_tags(["critical", "finance"])
    assert f.required_tags == ["critical", "finance"]


def test_apply_empty_pipeline_list():
    f = TagFilter(required_tags=["critical"])
    assert f.apply([]) == []
