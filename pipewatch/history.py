"""Persistent check result history using a local SQLite database."""

import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pipewatch.monitor import CheckResult

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path.home() / ".pipewatch" / "history.db"


class CheckHistory:
    """Records and retrieves pipeline check results from a SQLite database."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS check_results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline    TEXT    NOT NULL,
                success     INTEGER NOT NULL,
                error_msg   TEXT,
                checked_at  TEXT    NOT NULL
            )
            """
        )
        self._conn.commit()

    def record(self, result: CheckResult) -> None:
        """Persist a CheckResult to the database."""
        checked_at = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO check_results (pipeline, success, error_msg, checked_at) "
            "VALUES (?, ?, ?, ?)",
            (
                result.pipeline_name,
                int(result.success),
                result.error_message,
                checked_at,
            ),
        )
        self._conn.commit()
        logger.debug("Recorded result for '%s' (success=%s)", result.pipeline_name, result.success)

    def get_recent(self, pipeline_name: str, limit: int = 10) -> list[dict]:
        """Return the most recent check results for a pipeline."""
        cursor = self._conn.execute(
            "SELECT pipeline, success, error_msg, checked_at "
            "FROM check_results WHERE pipeline = ? "
            "ORDER BY id DESC LIMIT ?",
            (pipeline_name, limit),
        )
        rows = cursor.fetchall()
        return [
            {
                "pipeline": r[0],
                "success": bool(r[1]),
                "error_message": r[2],
                "checked_at": r[3],
            }
            for r in rows
        ]

    def last_failure(self, pipeline_name: str) -> Optional[dict]:
        """Return the most recent failure for a pipeline, or None."""
        cursor = self._conn.execute(
            "SELECT pipeline, success, error_msg, checked_at "
            "FROM check_results WHERE pipeline = ? AND success = 0 "
            "ORDER BY id DESC LIMIT 1",
            (pipeline_name,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"pipeline": row[0], "success": False, "error_message": row[2], "checked_at": row[3]}

    def close(self) -> None:
        self._conn.close()
