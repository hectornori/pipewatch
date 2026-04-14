"""Unit tests for QuotaConfig and helpers."""
import pytest

from pipewatch.quota_config import QuotaConfig, quota_config_from_dict, wrap_with_quota
from pipewatch.notifiers.quota_notifier import QuotaNotifier


def test_valid_config_creates_successfully() -> None:
    cfg = QuotaConfig(max_count=5, window_seconds=600)
    assert cfg.max_count == 5
    assert cfg.window_seconds == 600


def test_invalid_max_count_raises() -> None:
    with pytest.raises(ValueError, match="max_count"):
        QuotaConfig(max_count=0, window_seconds=600)


def test_invalid_window_seconds_raises() -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        QuotaConfig(max_count=5, window_seconds=0)


def test_from_dict_minimal() -> None:
    cfg = quota_config_from_dict({"max_count": 10, "window_seconds": 3600})
    assert cfg.max_count == 10
    assert cfg.window_seconds == 3600
    assert cfg.db_path == ":memory:"


def test_from_dict_with_db_path() -> None:
    cfg = quota_config_from_dict({"max_count": 2, "window_seconds": 60, "db_path": "/tmp/q.db"})
    assert cfg.db_path == "/tmp/q.db"


def test_from_dict_missing_max_count_raises() -> None:
    with pytest.raises(KeyError, match="max_count"):
        quota_config_from_dict({"window_seconds": 3600})


def test_from_dict_missing_window_seconds_raises() -> None:
    with pytest.raises(KeyError, match="window_seconds"):
        quota_config_from_dict({"max_count": 5})


def test_wrap_with_quota_returns_quota_notifier() -> None:
    from dataclasses import dataclass

    @dataclass
    class _Stub:
        def send(self, result: object) -> None:
            pass

    cfg = QuotaConfig(max_count=5, window_seconds=300)
    wrapped = wrap_with_quota(_Stub(), cfg)
    assert isinstance(wrapped, QuotaNotifier)
    assert wrapped.max_count == 5
    assert wrapped.window_seconds == 300
