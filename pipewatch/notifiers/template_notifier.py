"""Notifier that renders alert messages from a Jinja2-style template before forwarding."""
from __future__ import annotations

from dataclasses import dataclass, field
from string import Template
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: object) -> None:
        ...


# Default templates used when the caller does not supply custom ones.
_DEFAULT_SUCCESS = "[OK] ${pipeline} completed successfully."
_DEFAULT_FAILURE = "[FAIL] ${pipeline} failed: ${error}"


@dataclass
class TemplateNotifier:
    """Wrap an inner notifier and rewrite the result's message via a template.

    Template variables available:
        ${pipeline}  – pipeline name
        ${error}     – error message (empty string on success)
        ${status}    – 'ok' or 'fail'
    """

    inner: Notifier
    success_template: str = _DEFAULT_SUCCESS
    failure_template: str = _DEFAULT_FAILURE

    def send(self, result: object) -> None:
        rendered = self._render(result)
        # Attach the rendered text as a display_message attribute so downstream
        # notifiers (e.g. Slack, email) can use it if they choose.
        try:
            result.__dict__["display_message"] = rendered  # type: ignore[union-attr]
        except AttributeError:
            pass
        self.inner.send(result)

    def _render(self, result: object) -> str:
        pipeline = getattr(result, "pipeline_name", "unknown")
        error = getattr(result, "error_message", None) or ""
        success = not bool(error)
        status = "ok" if success else "fail"
        template_str = self.success_template if success else self.failure_template
        return Template(template_str).safe_substitute(
            pipeline=pipeline,
            error=error,
            status=status,
        )


def template_notifier_from_config(inner: Notifier, cfg: dict) -> TemplateNotifier:
    """Construct a TemplateNotifier from a config mapping."""
    return TemplateNotifier(
        inner=inner,
        success_template=cfg.get("success_template", _DEFAULT_SUCCESS),
        failure_template=cfg.get("failure_template", _DEFAULT_FAILURE),
    )
