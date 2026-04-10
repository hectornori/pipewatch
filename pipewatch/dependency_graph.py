"""Tracks pipeline dependencies and detects upstream failures."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class DependencyGraph:
    """Directed graph of pipeline dependencies.

    An edge A -> B means pipeline B depends on pipeline A
    (i.e. A is upstream of B).
    """

    _deps: Dict[str, Set[str]] = field(default_factory=dict)  # pipeline -> its upstream deps

    def add_dependency(self, pipeline: str, depends_on: str) -> None:
        """Record that *pipeline* depends on *depends_on*."""
        self._deps.setdefault(pipeline, set()).add(depends_on)

    def upstream_of(self, pipeline: str) -> Set[str]:
        """Return the direct upstream dependencies of *pipeline*."""
        return set(self._deps.get(pipeline, set()))

    def all_upstream_of(self, pipeline: str, _visited: Optional[Set[str]] = None) -> Set[str]:
        """Return all transitive upstream dependencies of *pipeline*."""
        if _visited is None:
            _visited = set()
        for dep in self._deps.get(pipeline, set()):
            if dep not in _visited:
                _visited.add(dep)
                self.all_upstream_of(dep, _visited)
        return _visited

    def has_failed_upstream(self, pipeline: str, failed_pipelines: Set[str]) -> bool:
        """Return True if any transitive upstream dependency is in *failed_pipelines*."""
        return bool(self.all_upstream_of(pipeline) & failed_pipelines)

    def downstream_of(self, pipeline: str) -> List[str]:
        """Return pipelines that directly depend on *pipeline*."""
        return [p for p, deps in self._deps.items() if pipeline in deps]


def graph_from_config(pipelines: list) -> DependencyGraph:
    """Build a :class:`DependencyGraph` from a list of PipelineConfig objects.

    Each pipeline may carry a ``depends_on`` list of pipeline names.
    """
    graph = DependencyGraph()
    for pipeline in pipelines:
        depends_on: List[str] = getattr(pipeline, "depends_on", None) or []
        for dep in depends_on:
            graph.add_dependency(pipeline.name, dep)
    return graph
