import pandas as pd

from rules import apply_escalation_rules, apply_overdue_flags, calculate_kpis


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "T1",
                "task": "Task 1",
                "team": "Operations",
                "owner": "Owner A",
                "priority": "High",
                "status": "Open",
                "assigned_date": pd.Timestamp("2026-10-20"),
                "due_date": pd.Timestamp("2026-10-25"),
                "completed_date": pd.NaT,
            },
            {
                "task_id": "T2",
                "task": "Task 2",
                "team": "Operations",
                "owner": "Owner B",
                "priority": "Low",
                "status": "Open",
                "assigned_date": pd.Timestamp("2026-10-18"),
                "due_date": pd.Timestamp("2026-10-28"),
                "completed_date": pd.NaT,
            },
            {
                "task_id": "T3",
                "task": "Task 3",
                "team": "Support",
                "owner": "Owner C",
                "priority": "Medium",
                "status": "Closed",
                "assigned_date": pd.Timestamp("2026-10-10"),
                "due_date": pd.Timestamp("2026-10-15"),
                "completed_date": pd.Timestamp("2026-10-14"),
            },
        ]
    )


def test_overdue_logic_marks_open_overdue_only():
    df = apply_overdue_flags(_sample_df(), today=pd.Timestamp("2026-10-30"))

    assert bool(df.loc[df["task_id"] == "T1", "is_overdue"].item()) is True
    assert bool(df.loc[df["task_id"] == "T2", "is_overdue"].item()) is True
    assert bool(df.loc[df["task_id"] == "T3", "is_overdue"].item()) is False


def test_escalation_logic_uses_priority_and_day_thresholds():
    rules = {"high_priority_overdue_days": 0, "any_priority_overdue_days": 3}
    df = apply_escalation_rules(_sample_df(), rules, today=pd.Timestamp("2026-10-30"))

    assert bool(df.loc[df["task_id"] == "T1", "escalate"].item()) is True
    assert bool(df.loc[df["task_id"] == "T2", "escalate"].item()) is False


def test_kpi_logic_returns_expected_metrics():
    rules = {"high_priority_overdue_days": 0, "any_priority_overdue_days": 3}
    df = apply_escalation_rules(_sample_df(), rules, today=pd.Timestamp("2026-10-30"))
    metrics = calculate_kpis(df)

    assert metrics["total_tasks"] == 3
    assert metrics["completion_rate"] == 33.33
    assert metrics["overdue_tasks"] == 2
    assert metrics["on_time_rate"] == 100.0
    assert metrics["avg_turnaround_days"] == 4.0
