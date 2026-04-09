"""Pipeline monitor: runs checks and dispatches alerts on failure."""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from pipewatch.config import Config, PipelineConfig
from pipewatch.notifiers.slack import SlackNotifier
from pipewatch.notifiers.email import EmailNotifier

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    pipeline_name: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def error_message(self) -> Optional[str]:
        return self.stderr.strip() or None


class PipelineMonitor:
    """Executes pipeline health-check commands and routes alerts."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._slack: Optional[SlackNotifier] = (
            SlackNotifier(config.slack) if config.slack else None
        )
        self._email: Optional[EmailNotifier] = (
            EmailNotifier(config.email) if config.email else None
        )

    def run_all(self) -> List[CheckResult]:
        """Run checks for every enabled pipeline and return results."""
        results: List[CheckResult] = []
        for pipeline in self.config.get_enabled_pipelines():
            result = self._check(pipeline)
            results.append(result)
            if not result.success:
                self._alert(result)
        return results

    def _check(self, pipeline: PipelineConfig) -> CheckResult:
        logger.info("Checking pipeline '%s'", pipeline.name)
        start = datetime.utcnow()
        try:
            proc = subprocess.run(
                pipeline.check_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=pipeline.timeout_seconds,
            )
            duration = (datetime.utcnow() - start).total_seconds()
            return CheckResult(
                pipeline_name=pipeline.name,
                success=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_seconds=duration,
            )
        except subprocess.TimeoutExpired:
            duration = (datetime.utcnow() - start).total_seconds()
            return CheckResult(
                pipeline_name=pipeline.name,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Timed out after {pipeline.timeout_seconds}s",
                duration_seconds=duration,
            )

    def _alert(self, result: CheckResult) -> None:
        if self._slack:
            self._slack.send(
                pipeline_name=result.pipeline_name,
                error=result.error_message,
            )
        if self._email:
            self._email.send(
                pipeline_name=result.pipeline_name,
                error=result.error_message,
            )
