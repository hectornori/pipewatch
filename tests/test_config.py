"""Tests for configuration management."""

import pytest
import tempfile
import yaml
from pathlib import Path
from pipewatch.config import Config, PipelineConfig, SlackConfig, EmailConfig


def test_pipeline_config_creation():
    """Test creating a pipeline configuration."""
    pipeline = PipelineConfig(
        name="test_pipeline",
        check_command="echo 'success'",
        check_interval=600
    )
    assert pipeline.name == "test_pipeline"
    assert pipeline.check_interval == 600
    assert pipeline.enabled is True
    assert pipeline.timeout == 30


def test_slack_config_creation():
    """Test creating Slack configuration."""
    slack = SlackConfig(
        webhook_url="https://hooks.slack.com/services/XXX",
        channel="#alerts"
    )
    assert slack.webhook_url == "https://hooks.slack.com/services/XXX"
    assert slack.username == "PipeWatch"
    assert slack.enabled is True


def test_config_from_dict():
    """Test creating Config from dictionary."""
    data = {
        'log_level': 'DEBUG',
        'pipelines': [
            {'name': 'pipeline1', 'check_command': 'ls', 'check_interval': 300},
            {'name': 'pipeline2', 'check_command': 'pwd', 'enabled': False}
        ],
        'slack': {
            'webhook_url': 'https://hooks.slack.com/test',
            'channel': '#monitoring'
        }
    }
    
    config = Config.from_dict(data)
    assert config.log_level == 'DEBUG'
    assert len(config.pipelines) == 2
    assert config.pipelines[0].name == 'pipeline1'
    assert config.slack.webhook_url == 'https://hooks.slack.com/test'


def test_config_from_file():
    """Test loading configuration from YAML file."""
    config_data = {
        'log_level': 'INFO',
        'pipelines': [
            {'name': 'etl_job', 'check_command': 'python check.py'}
        ],
        'email': {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'from_email': 'alerts@example.com',
            'to_emails': ['admin@example.com']
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = Config.from_file(temp_path)
        assert config.log_level == 'INFO'
        assert len(config.pipelines) == 1
        assert config.email.smtp_host == 'smtp.gmail.com'
    finally:
        Path(temp_path).unlink()


def test_get_enabled_pipelines():
    """Test filtering enabled pipelines."""
    config = Config(
        pipelines=[
            PipelineConfig(name='p1', check_command='cmd1', enabled=True),
            PipelineConfig(name='p2', check_command='cmd2', enabled=False),
            PipelineConfig(name='p3', check_command='cmd3', enabled=True)
        ]
    )
    
    enabled = config.get_enabled_pipelines()
    assert len(enabled) == 2
    assert enabled[0].name == 'p1'
    assert enabled[1].name == 'p3'
