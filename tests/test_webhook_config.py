"""Tests for WebhookConfig and webhooks_from_config."""
import pytest

from pipewatch.webhook_config import WebhookConfig, webhooks_from_config


def test_from_dict_minimal():
    cfg = WebhookConfig.from_dict({"url": "https://example.com/hook"})
    assert cfg.url == "https://example.com/hook"
    assert cfg.headers == {}
    assert cfg.timeout == 10
    assert cfg.enabled is True


def test_from_dict_full():
    cfg = WebhookConfig.from_dict({
        "url": "https://hooks.example.com",
        "headers": {"Authorization": "Bearer token"},
        "timeout": 5,
        "enabled": False,
    })
    assert cfg.headers == {"Authorization": "Bearer token"}
    assert cfg.timeout == 5
    assert cfg.enabled is False


def test_from_dict_missing_url_raises():
    with pytest.raises(ValueError, match="url"):
        WebhookConfig.from_dict({"timeout": 3})


def test_webhooks_from_config_empty():
    assert webhooks_from_config([]) == []


def test_webhooks_from_config_multiple():
    raw = [
        {"url": "https://a.example.com"},
        {"url": "https://b.example.com", "timeout": 20},
    ]
    result = webhooks_from_config(raw)
    assert len(result) == 2
    assert result[0].url == "https://a.example.com"
    assert result[1].timeout == 20
