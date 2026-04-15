"""Tests for SignatureNotifier."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any

import pytest

from pipewatch.notifiers.signature_notifier import SignatureNotifier, _SignedResult


@dataclass
class _FakeResult:
    pipeline_name: str = "pipe-a"
    error_message: str | None = None
    success: bool = True


@dataclass
class _FakeNotifier:
    received: list[Any] = field(default_factory=list)

    def send(self, result: Any) -> None:
        self.received.append(result)


@pytest.fixture()
def inner() -> _FakeNotifier:
    return _FakeNotifier()


@pytest.fixture()
def notifier(inner: _FakeNotifier) -> SignatureNotifier:
    return SignatureNotifier(inner=inner, secret="test-secret")


@pytest.fixture()
def result() -> _FakeResult:
    return _FakeResult()


def _expected_sig(pipeline: str, error: str | None, secret: str) -> str:
    payload = json.dumps({"pipeline": pipeline, "error": error}, sort_keys=True)
    return hmac.new(secret.encode(), payload.encode(), digestmod=hashlib.sha256).hexdigest()


def test_send_forwards_to_inner(notifier: SignatureNotifier, inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier.send(result)
    assert len(inner.received) == 1


def test_forwarded_result_is_signed_wrapper(notifier: SignatureNotifier, inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier.send(result)
    assert isinstance(inner.received[0], _SignedResult)


def test_signature_in_metadata(notifier: SignatureNotifier, inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier.send(result)
    signed = inner.received[0]
    assert "hmac_signature" in signed.metadata


def test_signature_value_is_correct(notifier: SignatureNotifier, inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier.send(result)
    signed = inner.received[0]
    expected = _expected_sig(result.pipeline_name, result.error_message, "test-secret")
    assert signed.metadata["hmac_signature"] == expected


def test_signature_differs_for_different_pipelines(inner: _FakeNotifier) -> None:
    n = SignatureNotifier(inner=inner, secret="s")
    n.send(_FakeResult(pipeline_name="a"))
    n.send(_FakeResult(pipeline_name="b"))
    sigs = [r.metadata["hmac_signature"] for r in inner.received]
    assert sigs[0] != sigs[1]


def test_signature_differs_when_error_present(inner: _FakeNotifier) -> None:
    n = SignatureNotifier(inner=inner, secret="s")
    n.send(_FakeResult(error_message=None))
    n.send(_FakeResult(error_message="boom"))
    sigs = [r.metadata["hmac_signature"] for r in inner.received]
    assert sigs[0] != sigs[1]


def test_attributes_proxied_from_inner(notifier: SignatureNotifier, inner: _FakeNotifier, result: _FakeResult) -> None:
    notifier.send(result)
    signed = inner.received[0]
    assert signed.pipeline_name == result.pipeline_name
    assert signed.success == result.success


def test_existing_metadata_preserved(inner: _FakeNotifier) -> None:
    @dataclass
    class _RichResult:
        pipeline_name: str = "p"
        error_message: str | None = None

        @property
        def metadata(self) -> dict:
            return {"env": "prod"}

    n = SignatureNotifier(inner=inner, secret="s")
    n.send(_RichResult())
    meta = inner.received[0].metadata
    assert "env" in meta
    assert "hmac_signature" in meta
