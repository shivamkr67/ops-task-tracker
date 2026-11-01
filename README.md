# Operations Control Center

Operations Control Center is a Python Streamlit app for operations task tracking and daily reporting.

## Features

- Task management in SQLite with add, edit, assign, and close flows
- Dashboard KPI cards:
  - total tasks
  - completion rate
  - overdue tasks
  - on-time rate
  - average turnaround time
- Charts:
  - tasks by status
  - workload per owner
  - overdue trend by day
  - tasks by team
- SLA and escalation rules loaded from `rules_config.json`
- Filters by team, owner, priority, and assigned date range
- Export options:
  - formatted Excel report with sheets: Summary, By Owner, Overdue and Escalations, All Tasks
  - short daily summary text file
- Seed script to load 100 fake sample tasks
- Basic pytest coverage for overdue, escalation, and KPI logic

## Folder structure

- `app.py`
- `db.py`
- `rules.py`
- `report.py`
- `seed.py`
- `tests/`
- `requirements.txt`

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Seed sample data:

   ```bash
   python seed.py
   ```

4. Run the app:

   ```bash
   streamlit run app.py
   ```

5. Run tests:

   ```bash
   pytest -q
   ```

## Configurable escalation rules

Edit `rules_config.json`:

```json
{
  "high_priority_overdue_days": 0,
  "any_priority_overdue_days": 3
}
```

- High priority overdue tasks escalate when overdue days are greater than or equal to `high_priority_overdue_days`.
- Any task overdue by greater than or equal to `any_priority_overdue_days` also escalates.

## Screenshots

Add app screenshots here, for example:

- Dashboard view
- Task Management view
- Reports view
