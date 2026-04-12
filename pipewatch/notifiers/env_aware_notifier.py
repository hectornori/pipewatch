"""Notifier wrapper that suppresses or tags alerts based on the current environment."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

SUPPRESSED_ENVS: frozenset[str] = frozenset({"local", "test"})


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


@dataclass
class EnvAwareNotifier:
    """Wraps an inner notifier and either suppresses sending or prepends an
    environment tag to the pipeline name depending on the current environment.

    Args:
        inner: The underlying notifier to delegate to.
        environment: Name of the current deployment environment (e.g. "prod",
            "staging", "local").
        suppressed_envs: Set of environment names for which notifications are
            silently dropped.  Defaults to {"local", "test"}.
        tag_envs: When *True*, non-suppressed non-production environments will
            have their pipeline name prefixed with ``[<env>]`` so recipients
            know the alert originated outside production.
    """

    inner: Notifier
    environment: str = "prod"
    suppressed_envs: frozenset[str] = field(default_factory=lambda: SUPPRESSED_ENVS)
    tag_envs: bool = True

    def send(self, result: object) -> None:
        env = self.environment.lower()

        if env in self.suppressed_envs:
            logger.debug(
                "EnvAwareNotifier: suppressing notification for env=%s pipeline=%s",
                env,
                getattr(result, "pipeline_name", "<unknown>"),
            )
            return

        if self.tag_envs and env != "prod":
            result = self._tag_result(result, env)

        self.inner.send(result)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tag_result(result: object, env: str) -> object:
        """Return a shallow copy of *result* with the pipeline name prefixed."""
        original_name: str = getattr(result, "pipeline_name", "")
        if not original_name:
            return result

        tagged_name = f"[{env}] {original_name}"
        try:
            # dataclasses / namedtuples support _replace; plain objects use setattr
            tagged = result._replace(pipeline_name=tagged_name)  # type: ignore[attr-defined]
        except AttributeError:
            import copy

            tagged = copy.copy(result)
            object.__setattr__(tagged, "pipeline_name", tagged_name)
        return tagged
