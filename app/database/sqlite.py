import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.models.job import Job


class Database:
    """Small SQLite storage facade."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _execute(self, sql: str, params=()):
        return self.connection.execute(sql, params)

    def _create_tables(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, job_id TEXT NOT NULL,
            title TEXT NOT NULL, company TEXT, location TEXT, url TEXT NOT NULL,
            posted_time TEXT, keyword TEXT, created_at TEXT NOT NULL,
            UNIQUE(source, job_id), UNIQUE(url)
        );
        CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, enabled INTEGER NOT NULL, interval INTEGER);
        CREATE TABLE IF NOT EXISTS run_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, finished_at TEXT,
            jobs_found INTEGER NOT NULL DEFAULT 0, new_jobs INTEGER NOT NULL DEFAULT 0,
            duplicates INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL, error TEXT
        );
        """
        self.connection.executescript(schema)
        self.connection.commit()

    def add_job_if_new(self, job: Job) -> bool:
        cursor = self._execute(
            "INSERT OR IGNORE INTO jobs(source, job_id, title, company, location, url, posted_time, keyword, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job.source, job.job_id, job.title, job.company, job.location, job.url, job.posted_time, job.keyword, datetime.now(timezone.utc).isoformat()),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def start_run(self) -> int:
        cursor = self._execute("INSERT INTO run_history(started_at, status) VALUES (?, ?)", (datetime.now(timezone.utc).isoformat(), "running"))
        run_id = cursor.lastrowid
        self.connection.commit()
        return int(run_id)

    def finish_run(self, run_id: int, jobs_found: int, new_jobs: int, duplicates: int, status: str = "success", error: str | None = None) -> None:
        self._execute("UPDATE run_history SET finished_at=?, jobs_found=?, new_jobs=?, duplicates=?, status=?, error=? WHERE id=?", (datetime.now(timezone.utc).isoformat(), jobs_found, new_jobs, duplicates, status, error, run_id))
        self.connection.commit()

    def stats(self) -> dict[str, int]:
        jobs = self._execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        runs = self._execute("SELECT COUNT(*) FROM run_history").fetchone()[0]
        return {"jobs": jobs, "runs": runs}

    def clear_cache(self) -> None:
        self._execute("DELETE FROM jobs")
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()
