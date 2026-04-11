"""Configuration helpers for webhook notifier."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WebhookConfig:
    """Holds settings for a single webhook destination."""

    url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout: int = 10
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookConfig":
        if "url" not in data:
            raise ValueError("WebhookConfig requires a 'url' field")
        return cls(
            url=data["url"],
            headers=data.get("headers", {}),
            timeout=int(data.get("timeout", 10)),
            enabled=bool(data.get("enabled", True)),
        )


def webhooks_from_config(raw: list[dict[str, Any]]) -> list[WebhookConfig]:
    """Parse a list of raw webhook config dicts into WebhookConfig objects."""
    return [WebhookConfig.from_dict(entry) for entry in raw]
