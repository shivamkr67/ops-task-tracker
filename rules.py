import json
from pathlib import Path

import numpy as np
import pandas as pd

RULES_PATH = Path(__file__).resolve().parent / "rules_config.json"


def load_rules(path: Path | str = RULES_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def apply_overdue_flags(df: pd.DataFrame, today: pd.Timestamp | None = None) -> pd.DataFrame:
    if df.empty:
        data = df.copy()
        data["days_overdue"] = pd.Series(dtype=int)
        data["is_overdue"] = pd.Series(dtype=bool)
        return data

    today = pd.Timestamp(today or pd.Timestamp.today().date())
    data = df.copy()
    data["days_overdue"] = (today - data["due_date"]).dt.days
    data["is_overdue"] = (data["days_overdue"] > 0) & (data["status"].str.lower() != "closed")
    data.loc[~data["is_overdue"], "days_overdue"] = 0
    return data


def apply_escalation_rules(df: pd.DataFrame, rules: dict, today: pd.Timestamp | None = None) -> pd.DataFrame:
    data = apply_overdue_flags(df, today=today)
    if data.empty:
        data["escalate"] = False
        data["escalation_reason"] = ""
        return data

    high_priority_threshold = int(rules.get("high_priority_overdue_days", 0))
    any_priority_threshold = int(rules.get("any_priority_overdue_days", 3))

    high_priority_overdue = (
        (data["priority"].str.lower() == "high") & (data["days_overdue"] >= high_priority_threshold)
    )
    any_priority_overdue = data["days_overdue"] >= any_priority_threshold

    data["escalate"] = data["is_overdue"] & (high_priority_overdue | any_priority_overdue)
    data["escalation_reason"] = np.where(
        data["escalate"] & high_priority_overdue,
        "High priority overdue",
        np.where(
            data["escalate"] & any_priority_overdue,
            f"Overdue by {any_priority_threshold}+ days",
            "",
        ),
    )
    return data


def calculate_kpis(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {
            "total_tasks": 0,
            "completion_rate": 0.0,
            "overdue_tasks": 0,
            "on_time_rate": 0.0,
            "avg_turnaround_days": 0.0,
        }

    total_tasks = int(len(df))
    closed = df[df["status"].str.lower() == "closed"].copy()
    completion_rate = float((len(closed) / total_tasks) * 100)

    overdue_tasks = int(df.get("is_overdue", pd.Series(False, index=df.index)).sum())

    if closed.empty:
        on_time_rate = 0.0
        avg_turnaround = 0.0
    else:
        closed["on_time"] = closed["completed_date"] <= closed["due_date"]
        on_time_rate = float(closed["on_time"].mean() * 100)

        turnaround = (closed["completed_date"] - closed["assigned_date"]).dt.days
        avg_turnaround = float(turnaround.mean()) if not turnaround.empty else 0.0

    return {
        "total_tasks": total_tasks,
        "completion_rate": round(completion_rate, 2),
        "overdue_tasks": overdue_tasks,
        "on_time_rate": round(on_time_rate, 2),
        "avg_turnaround_days": round(avg_turnaround, 2),
    }
