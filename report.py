from io import BytesIO

import pandas as pd
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


def _auto_fit_headers(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame) -> None:
    worksheet = writer.sheets[sheet_name]
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for index, column in enumerate(df.columns, start=1):
        lengths = [len(str(column))] + [len(str(v)) for v in df[column].fillna("")]
        max_value = max(lengths) if lengths else len(str(column))
        worksheet.column_dimensions[get_column_letter(index)].width = min(max_value + 2, 45)


def build_excel_report(df: pd.DataFrame, kpis: dict[str, float]) -> BytesIO:
    output = BytesIO()
    data = df.copy()
    for column, default in {"is_overdue": False, "escalate": False}.items():
        if column not in data.columns:
            data[column] = default

    summary_df = pd.DataFrame(
        {
            "Metric": [
                "Total Tasks",
                "Completion Rate",
                "Overdue Tasks",
                "On-time Rate",
                "Average Turnaround (Days)",
            ],
            "Value": [
                kpis["total_tasks"],
                f"{kpis['completion_rate']}%",
                kpis["overdue_tasks"],
                f"{kpis['on_time_rate']}%",
                kpis["avg_turnaround_days"],
            ],
        }
    )

    owner_summary = (
        data.groupby("owner", dropna=False)
        .agg(
            total_tasks=("task_id", "count"),
            open_tasks=("status", lambda x: (x.str.lower() != "closed").sum()),
            closed_tasks=("status", lambda x: (x.str.lower() == "closed").sum()),
            overdue_tasks=("is_overdue", "sum"),
            escalations=("escalate", "sum"),
        )
        .reset_index()
    )

    overdue_escalations = data[(data["is_overdue"]) | (data["escalate"])].copy()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        _auto_fit_headers(writer, "Summary", summary_df)

        owner_summary.to_excel(writer, sheet_name="By Owner", index=False)
        _auto_fit_headers(writer, "By Owner", owner_summary)

        overdue_escalations.to_excel(writer, sheet_name="Overdue and Escalations", index=False)
        _auto_fit_headers(writer, "Overdue and Escalations", overdue_escalations)

        data.to_excel(writer, sheet_name="All Tasks", index=False)
        _auto_fit_headers(writer, "All Tasks", data)

    output.seek(0)
    return output


def generate_daily_summary_text(kpis: dict[str, float], df: pd.DataFrame) -> str:
    escalated_count = int(df.get("escalate", pd.Series(False)).sum())
    top_overdue = df[df.get("is_overdue", False)]["task"].head(3).tolist()
    top_overdue_text = ", ".join(top_overdue) if top_overdue else "No overdue tasks"

    return (
        f"Daily Operations Summary\n"
        f"Total tasks: {kpis['total_tasks']}\n"
        f"Completion rate: {kpis['completion_rate']}%\n"
        f"Overdue tasks: {kpis['overdue_tasks']}\n"
        f"On-time rate: {kpis['on_time_rate']}%\n"
        f"Escalations: {escalated_count}\n"
        f"Top overdue items: {top_overdue_text}"
    )
