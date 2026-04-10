"""Configuration management for pipewatch."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class SlackConfig:
    """Slack notification configuration."""
    webhook_url: str
    channel: Optional[str] = None
    username: str = "PipeWatch"
    enabled: bool = True


@dataclass
class EmailConfig:
    """Email notification configuration."""
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    to_emails: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class PipelineConfig:
    """Individual pipeline configuration."""
    name: str
    check_command: str
    check_interval: int = 300  # seconds
    timeout: int = 30  # seconds
    enabled: bool = True


@dataclass
class Config:
    """Main application configuration."""
    pipelines: List[PipelineConfig] = field(default_factory=list)
    slack: Optional[SlackConfig] = None
    email: Optional[EmailConfig] = None
    log_level: str = "INFO"

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            raise ValueError(f"Config file must contain a YAML mapping, got: {type(data).__name__}")

        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Config":
        """Create Config from dictionary."""
        pipelines = []
        for p in data.get('pipelines', []):
            try:
                pipelines.append(PipelineConfig(**p))
            except TypeError as e:
                raise ValueError(f"Invalid pipeline configuration: {e}") from e
        
        slack = None
        if 'slack' in data:
            try:
                slack = SlackConfig(**data['slack'])
            except TypeError as e:
                raise ValueError(f"Invalid Slack configuration: {e}") from e
        
        email = None
        if 'email' in data:
            try:
                email = EmailConfig(**data['email'])
            except TypeError as e:
                raise ValueError(f"Invalid email configuration: {e}") from e
        
        return cls(
            pipelines=pipelines,
            slack=slack,
            email=email,
            log_level=data.get('log_level', 'INFO')
        )
    
    def get_enabled_pipelines(self) -> List[PipelineConfig]:
        """Return list of enabled pipelines."""
        return [p for p in self.pipelines if p.enabled]
