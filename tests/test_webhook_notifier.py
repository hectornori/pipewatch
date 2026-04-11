"""Tests for WebhookNotifier."""
from __future__ import annotations

import json
import urllib.error
from dataclasses import dataclass
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.notifiers.webhook_notifier import WebhookNotifier


@dataclass
class _FakeResult:
    pipeline_name: str = "my_pipeline"
    success: bool = True
    error_message: str | None = None


@pytest.fixture
def notifier():
    return WebhookNotifier(url="https://hooks.example.com/test")


def _mock_response(status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    resp.status = status
    return resp


def test_build_payload_success(notifier):
    result = _FakeResult(pipeline_name="etl_job", success=True, error_message=None)
    payload = notifier._build_payload(result)
    assert payload == {"pipeline": "etl_job", "success": True, "error": None}


def test_build_payload_failure(notifier):
    result = _FakeResult(pipeline_name="etl_job", success=False, error_message="boom")
    payload = notifier._build_payload(result)
    assert payload["error"] == "boom"
    assert payload["success"] is False


def test_send_success(notifier):
    result = _FakeResult()
    with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
        notifier.send(result)
    mock_open.assert_called_once()
    req = mock_open.call_args[0][0]
    assert req.full_url == "https://hooks.example.com/test"
    body = json.loads(req.data)
    assert body["pipeline"] == "my_pipeline"


def test_send_includes_custom_headers():
    n = WebhookNotifier(
        url="https://hooks.example.com/test",
        headers={"X-Api-Key": "secret"},
    )
    with patch("urllib.request.urlopen", return_value=_mock_response()) as mock_open:
        n.send(_FakeResult())
    req = mock_open.call_args[0][0]
    assert req.get_header("X-api-key") == "secret"


def test_send_raises_on_http_error(notifier):
    err = urllib.error.HTTPError(
        url="https://hooks.example.com/test",
        code=500,
        msg="Server Error",
        hdrs={},  # type: ignore[arg-type]
        fp=BytesIO(b""),
    )
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(urllib.error.HTTPError):
            notifier.send(_FakeResult())


def test_send_raises_on_url_error(notifier):
    err = urllib.error.URLError(reason="connection refused")
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(urllib.error.URLError):
            notifier.send(_FakeResult())
