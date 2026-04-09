"""Simple cron-style scheduler for periodic pipeline checks."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class ScheduledJob:
    """Represents a job to be run on a fixed interval."""

    name: str
    interval_seconds: int
    callback: Callable[[], None]
    _last_run: Optional[float] = field(default=None, init=False, repr=False)

    def is_due(self, now: float) -> bool:
        """Return True if the job should run at the given timestamp."""
        if self._last_run is None:
            return True
        return (now - self._last_run) >= self.interval_seconds

    def run(self) -> None:
        """Execute the callback and record the run time."""
        logger.info("Running scheduled job: %s", self.name)
        try:
            self.callback()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Job '%s' raised an exception: %s", self.name, exc)
        finally:
            self._last_run = time.monotonic()


class Scheduler:
    """Runs registered jobs when their interval has elapsed."""

    def __init__(self, tick_interval: float = 1.0) -> None:
        self._jobs: list[ScheduledJob] = []
        self.tick_interval = tick_interval

    def register(self, name: str, interval_seconds: int, callback: Callable[[], None]) -> None:
        """Add a new job to the scheduler."""
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be a positive integer")
        job = ScheduledJob(name=name, interval_seconds=interval_seconds, callback=callback)
        self._jobs.append(job)
        logger.debug("Registered job '%s' with interval %ds", name, interval_seconds)

    def tick(self) -> None:
        """Check all jobs and run any that are due."""
        now = time.monotonic()
        for job in self._jobs:
            if job.is_due(now):
                job.run()

    def run_forever(self) -> None:  # pragma: no cover
        """Block and run the scheduler loop indefinitely."""
        logger.info("Scheduler started (tick every %.1fs)", self.tick_interval)
        while True:
            self.tick()
            time.sleep(self.tick_interval)
