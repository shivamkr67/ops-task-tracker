from datetime import date
from uuid import uuid4

import pandas as pd
import plotly.express as px
import streamlit as st

from db import add_task, close_task, fetch_tasks, get_task, init_db, update_task
from report import build_excel_report, generate_daily_summary_text
from rules import apply_escalation_rules, calculate_kpis, load_rules

st.set_page_config(page_title="Operations Control Center", layout="wide")
st.title("Operations Control Center")

init_db()
rules = load_rules()

# Demo mode: if the database is empty (for example on a fresh deploy), load sample data
if fetch_tasks().empty:
    from seed import seed_tasks

    seed_tasks(100)

st.sidebar.header("Filters")
raw_df = fetch_tasks()
teams = ["All"] + sorted(raw_df["team"].dropna().unique().tolist()) if not raw_df.empty else ["All"]
owners = ["All"] + sorted(raw_df["owner"].dropna().unique().tolist()) if not raw_df.empty else ["All"]
priorities = ["All"] + sorted(raw_df["priority"].dropna().unique().tolist()) if not raw_df.empty else ["All"]

team_filter = st.sidebar.selectbox("Team", teams)
owner_filter = st.sidebar.selectbox("Owner", owners)
priority_filter = st.sidebar.selectbox("Priority", priorities)
# Default date range covers all tasks in the database
if raw_df.empty:
    default_start, default_end = date.today().replace(day=1), date.today()
else:
    default_start = raw_df["assigned_date"].min().date()
    default_end = max(raw_df["assigned_date"].max().date(), date.today())

date_range = st.sidebar.date_input(
    "Assigned date range",
    value=(default_start, default_end),
)

filters = {
    "team": team_filter,
    "owner": owner_filter,
    "priority": priority_filter,
}
if isinstance(date_range, tuple) and len(date_range) == 2:
    filters["start_date"], filters["end_date"] = date_range

df = fetch_tasks(filters=filters)
df = apply_escalation_rules(df, rules)
kpis = calculate_kpis(df)

page = st.radio("Page", ["Dashboard", "Task Management", "Reports"], horizontal=True)

if page == "Dashboard":
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tasks", kpis["total_tasks"])
    col2.metric("Completion Rate", f"{kpis['completion_rate']}%")
    col3.metric("Overdue Tasks", kpis["overdue_tasks"])
    col4.metric("On-time Rate", f"{kpis['on_time_rate']}%")
    col5.metric("Avg Turnaround", f"{kpis['avg_turnaround_days']} days")

    if not df.empty:
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.plotly_chart(px.pie(df, names="status", title="Tasks by Status"), width="stretch")
            st.plotly_chart(
                px.bar(df.groupby("team").size().reset_index(name="tasks"), x="team", y="tasks", title="Tasks by Team"),
                width="stretch",
            )

        with chart_col2:
            owner_load = df.groupby("owner").size().reset_index(name="tasks")
            st.plotly_chart(px.bar(owner_load, x="owner", y="tasks", title="Workload per Owner"), width="stretch")

            overdue_trend = (
                df[df["is_overdue"]]
                .groupby(df[df["is_overdue"]]["due_date"].dt.date)
                .size()
                .reset_index(name="overdue_tasks")
            )
            if overdue_trend.empty:
                st.info("No overdue trend data yet.")
            else:
                st.plotly_chart(
                    px.line(overdue_trend, x="due_date", y="overdue_tasks", title="Overdue Trend by Day"),
                    width="stretch",
                )

    st.subheader("Task Table")
    st.dataframe(df, width="stretch")

elif page == "Task Management":
    with st.expander("Add Task", expanded=True):
        with st.form("add_task_form"):
            task = st.text_input("Task")
            team = st.text_input("Team")
            owner = st.text_input("Owner")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            status = st.selectbox("Status", ["Open", "In Progress", "Blocked", "Closed"])
            assigned_date = st.date_input("Assigned Date", value=date.today())
            due_date = st.date_input("Due Date", value=date.today())
            submitted = st.form_submit_button("Add Task")

            if submitted and task.strip() and team.strip() and owner.strip():
                add_task(
                    {
                        "task_id": f"T-{uuid4().hex[:8].upper()}",
                        "task": task.strip(),
                        "team": team.strip(),
                        "owner": owner.strip(),
                        "priority": priority,
                        "status": status,
                        "assigned_date": str(assigned_date),
                        "due_date": str(due_date),
                        "completed_date": str(assigned_date) if status == "Closed" else None,
                    }
                )
                st.success("Task added")

    tasks_df = fetch_tasks()
    if tasks_df.empty:
        st.info("No tasks available to edit yet.")
    else:
        task_id = st.selectbox("Select Task ID", tasks_df["task_id"].tolist())
        selected_task = get_task(task_id)
        if selected_task:
            with st.form("edit_task_form"):
                new_task = st.text_input("Task", value=selected_task["task"])
                new_team = st.text_input("Team", value=selected_task["team"])
                new_owner = st.text_input("Owner", value=selected_task["owner"])
                new_priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(selected_task["priority"]))
                new_status = st.selectbox(
                    "Status",
                    ["Open", "In Progress", "Blocked", "Closed"],
                    index=["Open", "In Progress", "Blocked", "Closed"].index(selected_task["status"]),
                )
                new_assigned = st.date_input("Assigned Date", value=pd.to_datetime(selected_task["assigned_date"]).date())
                new_due = st.date_input("Due Date", value=pd.to_datetime(selected_task["due_date"]).date())

                c1, c2 = st.columns(2)
                save = c1.form_submit_button("Save Updates")
                mark_closed = c2.form_submit_button("Mark Closed")

                if save:
                    completed = date.today().isoformat() if new_status == "Closed" else None
                    update_task(
                        task_id,
                        {
                            "task": new_task,
                            "team": new_team,
                            "owner": new_owner,
                            "priority": new_priority,
                            "status": new_status,
                            "assigned_date": str(new_assigned),
                            "due_date": str(new_due),
                            "completed_date": completed,
                        },
                    )
                    st.success("Task updated")

                if mark_closed:
                    close_task(task_id, date.today().isoformat())
                    st.success("Task closed")

elif page == "Reports":
    st.subheader("Export")
    excel_bytes = build_excel_report(df, kpis)
    daily_summary = generate_daily_summary_text(kpis, df)

    st.download_button(
        "Download Excel Report",
        data=excel_bytes,
        file_name="operations_control_center_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.download_button(
        "Download Daily Summary",
        data=daily_summary,
        file_name="daily_summary.txt",
        mime="text/plain",
    )

    st.text_area("Preview Daily Summary", value=daily_summary, height=200)
