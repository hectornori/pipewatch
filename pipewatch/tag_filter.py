"""Tag-based filtering for pipelines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.config import PipelineConfig


@dataclass
class TagFilter:
    """Filter pipelines by one or more tags.

    A pipeline matches if it carries *all* of the required tags.
    When ``required_tags`` is empty every pipeline is considered a match.
    """

    required_tags: List[str] = field(default_factory=list)

    def matches(self, pipeline: PipelineConfig) -> bool:
        """Return True when *pipeline* satisfies the tag requirements."""
        if not self.required_tags:
            return True
        pipeline_tags = set(getattr(pipeline, "tags", None) or [])
        return all(tag in pipeline_tags for tag in self.required_tags)

    def apply(self, pipelines: List[PipelineConfig]) -> List[PipelineConfig]:
        """Return the subset of *pipelines* that match all required tags."""
        return [p for p in pipelines if self.matches(p)]


def filter_from_tags(tags: Optional[List[str]]) -> TagFilter:
    """Construct a :class:`TagFilter` from a list of tag strings.

    Passing *None* or an empty list produces a filter that matches everything.

    >>> f = filter_from_tags(["critical"])
    >>> f.required_tags
    ['critical']
    """
    return TagFilter(required_tags=list(tags) if tags else [])
