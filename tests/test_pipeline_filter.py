"""Tests for pipewatch.pipeline_filter."""
import pytest

from pipewatch.config import PipelineConfig
from pipewatch.pipeline_filter import PipelineFilter, filter_from_args


def _make_pipeline(name: str, enabled: bool = True, tags=None) -> PipelineConfig:
    p = PipelineConfig(name=name, command="echo ok", schedule=60, enabled=enabled)
    # Attach tags as an ad-hoc attribute so the filter can read them.
    object.__setattr__(p, "tags", tags or [])
    return p


@pytest.fixture()
def pipelines():
    return [
        _make_pipeline("ingest", enabled=True, tags=["etl", "daily"]),
        _make_pipeline("transform", enabled=True, tags=["etl"]),
        _make_pipeline("report", enabled=False, tags=["reporting"]),
        _make_pipeline("cleanup", enabled=True, tags=[]),
    ]


def test_enabled_only_excludes_disabled(pipelines):
    f = PipelineFilter(enabled_only=True)
    result = f.apply(pipelines)
    assert all(p.enabled for p in result)
    assert len(result) == 3


def test_disabled_included_when_flag_off(pipelines):
    f = PipelineFilter(enabled_only=False)
    assert len(f.apply(pipelines)) == 4


def test_filter_by_name(pipelines):
    f = PipelineFilter(names=["ingest", "cleanup"], enabled_only=False)
    names = [p.name for p in f.apply(pipelines)]
    assert names == ["ingest", "cleanup"]


def test_filter_by_name_respects_enabled(pipelines):
    # 'report' is disabled; with enabled_only=True it should be excluded
    f = PipelineFilter(names=["report", "ingest"], enabled_only=True)
    names = [p.name for p in f.apply(pipelines)]
    assert names == ["ingest"]


def test_filter_by_tag(pipelines):
    f = PipelineFilter(tags=["etl"], enabled_only=False)
    names = {p.name for p in f.apply(pipelines)}
    assert names == {"ingest", "transform"}


def test_filter_by_tag_any_match(pipelines):
    f = PipelineFilter(tags=["daily", "reporting"], enabled_only=False)
    names = {p.name for p in f.apply(pipelines)}
    assert names == {"ingest", "report"}


def test_no_criteria_returns_enabled(pipelines):
    f = PipelineFilter()
    result = f.apply(pipelines)
    assert len(result) == 3


def test_filter_from_args_defaults():
    f = filter_from_args()
    assert f.names == []
    assert f.tags == []
    assert f.enabled_only is True


def test_filter_from_args_with_values(pipelines):
    f = filter_from_args(names=["ingest"], tags=["etl"], enabled_only=True)
    result = f.apply(pipelines)
    assert len(result) == 1
    assert result[0].name == "ingest"


def test_matches_returns_false_for_disabled_default():
    p = _make_pipeline("x", enabled=False)
    f = PipelineFilter()
    assert f.matches(p) is False


def test_matches_returns_true_for_enabled_no_criteria():
    p = _make_pipeline("x", enabled=True)
    f = PipelineFilter()
    assert f.matches(p) is True
