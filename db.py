import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "operations.db"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    task TEXT NOT NULL,
    team TEXT NOT NULL,
    owner TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    completed_date TEXT
);
"""


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(str(db_path))


def init_db(db_path: Path | str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(SCHEMA_SQL)
        conn.commit()


def add_task(task_data: dict[str, Any], db_path: Path | str = DB_PATH) -> None:
    columns = [
        "task_id",
        "task",
        "team",
        "owner",
        "priority",
        "status",
        "assigned_date",
        "due_date",
        "completed_date",
    ]
    values = [task_data.get(col) for col in columns]
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO tasks (
                task_id, task, team, owner, priority, status,
                assigned_date, due_date, completed_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        conn.commit()


def update_task(task_id: str, updates: dict[str, Any], db_path: Path | str = DB_PATH) -> None:
    allowed = {
        "task",
        "team",
        "owner",
        "priority",
        "status",
        "assigned_date",
        "due_date",
        "completed_date",
    }
    clean_updates = {k: v for k, v in updates.items() if k in allowed}
    if not clean_updates:
        return

    set_clause = ", ".join([f"{column} = ?" for column in clean_updates])
    values = list(clean_updates.values()) + [task_id]

    with get_connection(db_path) as conn:
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE task_id = ?", values)
        conn.commit()


def close_task(task_id: str, completed_date: str, db_path: Path | str = DB_PATH) -> None:
    update_task(
        task_id,
        {
            "status": "Closed",
            "completed_date": completed_date,
        },
        db_path=db_path,
    )


def get_task(task_id: str, db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        columns = [c[1] for c in conn.execute("PRAGMA table_info(tasks)").fetchall()]
        return dict(zip(columns, row))


def fetch_tasks(filters: dict[str, Any] | None = None, db_path: Path | str = DB_PATH) -> pd.DataFrame:
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list[Any] = []

    if filters:
        if filters.get("team") and filters["team"] != "All":
            query += " AND team = ?"
            params.append(filters["team"])
        if filters.get("owner") and filters["owner"] != "All":
            query += " AND owner = ?"
            params.append(filters["owner"])
        if filters.get("priority") and filters["priority"] != "All":
            query += " AND priority = ?"
            params.append(filters["priority"])

    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        return df

    for column in ["assigned_date", "due_date", "completed_date"]:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    if filters and filters.get("start_date") and filters.get("end_date"):
        start_date = pd.to_datetime(filters["start_date"])
        end_date = pd.to_datetime(filters["end_date"])
        df = df[(df["assigned_date"] >= start_date) & (df["assigned_date"] <= end_date)]

    return df.sort_values("assigned_date", ascending=False)
