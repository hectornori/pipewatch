"""Notifier decorator that appends an HMAC-SHA256 signature to result metadata."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, result: Any) -> None:
        ...


@dataclass
class _SignedResult:
    """Wraps an existing result and exposes an HMAC signature in metadata."""

    _inner: Any
    _signature: str

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    @property
    def metadata(self) -> dict[str, Any]:
        base: dict[str, Any] = {}
        if hasattr(self._inner, "metadata"):
            base = dict(self._inner.metadata)
        base["hmac_signature"] = self._signature
        return base


@dataclass
class SignatureNotifier:
    """Wraps an inner notifier and signs each result with an HMAC-SHA256 digest.

    The signature is computed over a canonical JSON representation of the
    pipeline name and error_message (if any), keyed with *secret*.
    """

    inner: Notifier
    secret: str
    _algorithm: str = field(default="sha256", init=False)

    def _sign(self, result: Any) -> str:
        pipeline = getattr(result, "pipeline_name", "") or ""
        error = getattr(result, "error_message", None)
        payload = json.dumps({"pipeline": pipeline, "error": error}, sort_keys=True)
        return hmac.new(
            self.secret.encode(),
            payload.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

    def send(self, result: Any) -> None:
        signature = self._sign(result)
        signed = _SignedResult(_inner=result, _signature=signature)
        self.inner.send(signed)
