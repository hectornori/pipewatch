"""Tests for the pipewatch CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pipewatch.cli import cli
from pipewatch.config import Config, PipelineConfig
from pipewatch.monitor import CheckResult
from datetime import datetime


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def mock_config() -> Config:
    return Config(
        pipelines=[
            PipelineConfig(name="etl_orders", check_command="exit 0", enabled=True, timeout_seconds=10),
            PipelineConfig(name="etl_users", check_command="exit 0", enabled=False, timeout_seconds=10),
        ],
        slack=None,
        email=None,
    )


def _ok_result(name: str) -> CheckResult:
    return CheckResult(
        pipeline_name=name, success=True, exit_code=0,
        stdout="", stderr="", duration_seconds=0.1, timestamp=datetime.utcnow(),
    )


def _fail_result(name: str) -> CheckResult:
    return CheckResult(
        pipeline_name=name, success=False, exit_code=1,
        stdout="", stderr="error!", duration_seconds=0.2, timestamp=datetime.utcnow(),
    )


def test_run_all_success(runner, mock_config, tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("pipelines: []\n")
    with patch("pipewatch.cli.from_file", return_value=mock_config), \
         patch("pipewatch.cli.PipelineMonitor") as MockMonitor:
        MockMonitor.return_value.run_all.return_value = [_ok_result("etl_orders")]
        result = runner.invoke(cli, ["-c", str(cfg_file), "run"])
    assert result.exit_code == 0
    assert "All pipelines healthy" in result.output


def test_run_with_failures(runner, mock_config, tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("pipelines: []\n")
    with patch("pipewatch.cli.from_file", return_value=mock_config), \
         patch("pipewatch.cli.PipelineMonitor") as MockMonitor:
        MockMonitor.return_value.run_all.return_value = [_fail_result("etl_orders")]
        result = runner.invoke(cli, ["-c", str(cfg_file), "run"])
    assert result.exit_code == 1
    assert "1 pipeline(s) failed" in result.output


def test_list_pipelines(runner, mock_config, tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("pipelines: []\n")
    with patch("pipewatch.cli.from_file", return_value=mock_config):
        result = runner.invoke(cli, ["-c", str(cfg_file), "list"])
    assert result.exit_code == 0
    assert "etl_orders" in result.output
    assert "etl_users" in result.output


def test_missing_config_file(runner):
    result = runner.invoke(cli, ["-c", "nonexistent.yaml", "run"])
    assert result.exit_code == 1
    assert "not found" in result.output
