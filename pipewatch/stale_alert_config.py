"""Configuration helpers for :class:`StaleAlertNotifier`."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StaleAlertConfig:
    """Configuration for the stale-alert notifier wrapper.

    Parameters
    ----------
    stale_threshold_minutes:
        How many minutes without a successful run before a pipeline is
        considered stale.  Must be a positive integer.
    db_path:
        SQLite database path used by the underlying
        :class:`~pipewatch.checkpoint.CheckpointStore`.
    stale_only:
        When *True* (default) only the stale notifier is called for stale
        pipelines.  When *False* both notifiers receive the result.
    """

    stale_threshold_minutes: int = 60
    db_path: str = "pipewatch.db"
    stale_only: bool = True

    def __post_init__(self) -> None:
        if self.stale_threshold_minutes <= 0:
            raise ValueError(
                "stale_threshold_minutes must be a positive integer, "
                f"got {self.stale_threshold_minutes}"
            )
        if not self.db_path:
            raise ValueError("db_path must not be empty")


def stale_alert_config_from_dict(data: dict) -> StaleAlertConfig:
    """Build a :class:`StaleAlertConfig` from a raw mapping."""
    return StaleAlertConfig(
        stale_threshold_minutes=int(data.get("stale_threshold_minutes", 60)),
        db_path=str(data.get("db_path", "pipewatch.db")),
        stale_only=bool(data.get("stale_only", True)),
    )


def wrap_with_stale_alert(
    inner: object,
    stale_notifier: object,
    config: StaleAlertConfig,
) -> object:
    """Wrap *inner* with a :class:`~pipewatch.notifiers.stale_alert_notifier.StaleAlertNotifier`."""
    from pipewatch.checkpoint import CheckpointStore
    from pipewatch.stale_detector import StaleDetector
    from pipewatch.notifiers.stale_alert_notifier import StaleAlertNotifier

    store = CheckpointStore(db_path=config.db_path)
    detector = StaleDetector(
        store=store,
        threshold_minutes=config.stale_threshold_minutes,
    )
    return StaleAlertNotifier(
        inner=inner,  # type: ignore[arg-type]
        stale_notifier=stale_notifier,  # type: ignore[arg-type]
        detector=detector,
        stale_only=config.stale_only,
    )
