"""Tests for pipewatch.dependency_graph."""
from unittest.mock import MagicMock

import pytest

from pipewatch.dependency_graph import DependencyGraph, graph_from_config


@pytest.fixture()
def graph() -> DependencyGraph:
    g = DependencyGraph()
    # ingest -> transform -> report
    g.add_dependency("transform", "ingest")
    g.add_dependency("report", "transform")
    return g


def test_upstream_direct(graph: DependencyGraph) -> None:
    assert graph.upstream_of("transform") == {"ingest"}


def test_upstream_empty_for_root(graph: DependencyGraph) -> None:
    assert graph.upstream_of("ingest") == set()


def test_all_upstream_transitive(graph: DependencyGraph) -> None:
    assert graph.all_upstream_of("report") == {"transform", "ingest"}


def test_all_upstream_direct_only(graph: DependencyGraph) -> None:
    assert graph.all_upstream_of("transform") == {"ingest"}


def test_all_upstream_root_is_empty(graph: DependencyGraph) -> None:
    assert graph.all_upstream_of("ingest") == set()


def test_has_failed_upstream_true(graph: DependencyGraph) -> None:
    assert graph.has_failed_upstream("report", {"ingest"}) is True


def test_has_failed_upstream_false(graph: DependencyGraph) -> None:
    assert graph.has_failed_upstream("report", {"other"}) is False


def test_has_failed_upstream_no_deps() -> None:
    g = DependencyGraph()
    assert g.has_failed_upstream("standalone", {"ingest"}) is False


def test_downstream_of(graph: DependencyGraph) -> None:
    assert graph.downstream_of("transform") == ["report"]


def test_downstream_of_root(graph: DependencyGraph) -> None:
    assert graph.downstream_of("ingest") == ["transform"]


def test_downstream_of_leaf(graph: DependencyGraph) -> None:
    assert graph.downstream_of("report") == []


def test_add_multiple_dependencies() -> None:
    g = DependencyGraph()
    g.add_dependency("merge", "source_a")
    g.add_dependency("merge", "source_b")
    assert g.upstream_of("merge") == {"source_a", "source_b"}


def test_graph_from_config_builds_edges() -> None:
    p1 = MagicMock()
    p1.name = "ingest"
    p1.depends_on = []

    p2 = MagicMock()
    p2.name = "transform"
    p2.depends_on = ["ingest"]

    graph = graph_from_config([p1, p2])
    assert graph.upstream_of("transform") == {"ingest"}
    assert graph.upstream_of("ingest") == set()


def test_graph_from_config_none_depends_on() -> None:
    p = MagicMock()
    p.name = "solo"
    p.depends_on = None

    graph = graph_from_config([p])
    assert graph.upstream_of("solo") == set()
