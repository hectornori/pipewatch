"""Utilities for filtering pipelines by tag, name, or enabled status."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.config import PipelineConfig


@dataclass
class PipelineFilter:
    """Encapsulates criteria used to select a subset of pipelines."""

    names: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    enabled_only: bool = True

    def matches(self, pipeline: PipelineConfig) -> bool:
        """Return True if *pipeline* satisfies all active filter criteria."""
        if self.enabled_only and not pipeline.enabled:
            return False

        if self.names and pipeline.name not in self.names:
            return False

        if self.tags:
            pipeline_tags: List[str] = getattr(pipeline, "tags", []) or []
            if not any(tag in pipeline_tags for tag in self.tags):
                return False

        return True

    def apply(self, pipelines: List[PipelineConfig]) -> List[PipelineConfig]:
        """Return the subset of *pipelines* that match the filter."""
        return [p for p in pipelines if self.matches(p)]


def filter_from_args(
    names: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    enabled_only: bool = True,
) -> PipelineFilter:
    """Convenience constructor that accepts nullable lists from CLI args."""
    return PipelineFilter(
        names=names or [],
        tags=tags or [],
        enabled_only=enabled_only,
    )
