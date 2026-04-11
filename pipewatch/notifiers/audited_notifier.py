"""Notifier decorator that writes an audit entry for every alert dispatched."""
from __future__ import annotations

from typing import Protocol

from pipewatch.audit_log import AuditLog
from pipewatch.monitor import CheckResult


class Notifier(Protocol):
    def send(self, result: CheckResult) -> None:
        ...


class AuditedNotifier:
    """Wraps any Notifier and records each send() call in the AuditLog."""

    def __init__(self, inner: Notifier, audit_log: AuditLog, channel: str = "unknown") -> None:
        self._inner = inner
        self._log = audit_log
        self._channel = channel

    def send(self, result: CheckResult) -> None:
        try:
            self._inner.send(result)
            status = "sent"
        except Exception as exc:  # noqa: BLE001
            status = f"failed: {exc}"
            raise
        finally:
            detail = (
                f"channel={self._channel} status={status} "
                f"ok={result.ok} error={result.error_message!r}"
            )
            self._log.record(
                event_type="alert",
                pipeline_name=result.pipeline_name,
                detail=detail,
            )
