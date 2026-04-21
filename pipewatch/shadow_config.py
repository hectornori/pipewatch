"""Configuration helpers for ShadowNotifier."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ShadowConfig:
    """Parsed configuration for a shadow notifier pair."""
    enabled: bool = True
    log_divergence: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a bool")
        if not isinstance(self.log_divergence, bool):
            raise TypeError("log_divergence must be a bool")


def shadow_config_from_dict(data: dict[str, Any]) -> ShadowConfig:
    """Build a :class:`ShadowConfig` from a raw mapping (e.g. parsed YAML)."""
    return ShadowConfig(
        enabled=bool(data.get("enabled", True)),
        log_divergence=bool(data.get("log_divergence", False)),
    )


def wrap_with_shadow(
    primary: Any,
    shadow: Any,
    config: ShadowConfig | None = None,
) -> Any:
    """Wrap *primary* with a :class:`~pipewatch.notifiers.shadow_notifier.ShadowNotifier`.

    If *config* is provided and ``enabled`` is ``False`` the *primary* is
    returned unchanged.
    """
    from pipewatch.notifiers.shadow_notifier import ShadowNotifier

    if config is not None and not config.enabled:
        return primary
    return ShadowNotifier(primary=primary, shadow=shadow)
