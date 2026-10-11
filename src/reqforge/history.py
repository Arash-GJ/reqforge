"""Local execution history and deterministic regression comparison."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .core import Result


def default_db() -> Path:
    return Path.home() / ".reqforge" / "history.sqlite3"


def save_run(results: list[Result], db: Path | None = None) -> str:
    path = db or default_db()
    path.parent.mkdir(parents=True, exist_ok=True)
    run_id = uuid4().hex[:12]
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, results TEXT NOT NULL)")
        conn.execute("INSERT INTO runs VALUES (?, ?, ?)", (run_id, datetime.now(UTC).isoformat(), json.dumps([asdict(r) for r in results])))
    return run_id


def get_run(run_id: str, db: Path | None = None) -> list[Result]:
    path = db or default_db()
    if not path.is_file():
        raise ValueError("No execution history found")
    with sqlite3.connect(path) as conn:
        try:
            row = conn.execute("SELECT results FROM runs WHERE id = ?", (run_id,)).fetchone()
        except sqlite3.OperationalError as exc:
            raise ValueError("No execution history found") from exc
    if row is None:
        raise ValueError(f"Unknown run ID: {run_id}")
    return [Result(**item) for item in json.loads(row[0])]


def list_runs(db: Path | None = None) -> list[tuple[str, str, int]]:
    path = db or default_db()
    if not path.is_file():
        return []
    with sqlite3.connect(path) as conn:
        try:
            rows = conn.execute("SELECT id, created_at, results FROM runs ORDER BY created_at DESC").fetchall()
        except sqlite3.OperationalError:
            return []
    return [(run_id, created_at, len(json.loads(results))) for run_id, created_at, results in rows]


def compare_runs(before: list[Result], after: list[Result]) -> dict:
    """Compare by test name; duplicate names are rejected to avoid ambiguous results."""
    def index(items: list[Result]) -> dict[str, Result]:
        mapped = {item.name: item for item in items}
        if len(mapped) != len(items):
            raise ValueError("Duplicate test names cannot be compared")
        return mapped

    old, new = index(before), index(after)
    names = sorted(old.keys() | new.keys())
    return {
        "regressions": [n for n in names if n in old and n in new and old[n].passed and not new[n].passed],
        "fixes": [n for n in names if n in old and n in new and not old[n].passed and new[n].passed],
        "added": sorted(new.keys() - old.keys()),
        "removed": sorted(old.keys() - new.keys()),
        "status_changes": [n for n in names if n in old and n in new and old[n].status != new[n].status],
    }
