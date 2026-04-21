"""Unit tests focused on ShadowConfig validation and factory helpers."""
from __future__ import annotations

import pytest

from pipewatch.shadow_config import ShadowConfig, shadow_config_from_dict


def test_enabled_defaults_to_true():
    cfg = ShadowConfig()
    assert cfg.enabled is True


def test_log_divergence_defaults_to_false():
    cfg = ShadowConfig()
    assert cfg.log_divergence is False


def test_explicit_enabled_false():
    cfg = ShadowConfig(enabled=False)
    assert cfg.enabled is False


def test_explicit_log_divergence_true():
    cfg = ShadowConfig(log_divergence=True)
    assert cfg.log_divergence is True


def test_invalid_enabled_type_raises():
    with pytest.raises(TypeError):
        ShadowConfig(enabled="yes")  # type: ignore[arg-type]


def test_invalid_log_divergence_type_raises():
    with pytest.raises(TypeError):
        ShadowConfig(log_divergence=1)  # type: ignore[arg-type]


def test_from_dict_empty_uses_defaults():
    cfg = shadow_config_from_dict({})
    assert cfg.enabled is True
    assert cfg.log_divergence is False


def test_from_dict_sets_enabled_false():
    cfg = shadow_config_from_dict({"enabled": False})
    assert cfg.enabled is False


def test_from_dict_sets_log_divergence_true():
    cfg = shadow_config_from_dict({"log_divergence": True})
    assert cfg.log_divergence is True


def test_from_dict_ignores_unknown_keys():
    # Should not raise even with extra keys
    cfg = shadow_config_from_dict({"enabled": True, "unknown_key": "ignored"})
    assert cfg.enabled is True
