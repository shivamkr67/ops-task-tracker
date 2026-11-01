import random
from datetime import date, timedelta

from db import add_task, init_db

TEAMS = ["Operations", "Support", "Platform", "QA"]
OWNERS = ["Owner A", "Owner B", "Owner C", "Owner D", "Owner E"]
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Open", "In Progress", "Blocked", "Closed"]


def seed_tasks(total: int = 100) -> None:
    init_db()
    today = date.today()

    for i in range(total):
        assigned = today - timedelta(days=random.randint(1, 30))
        due = assigned + timedelta(days=random.randint(1, 14))
        status = random.choice(STATUSES)
        completed = None

        if status == "Closed":
            completed = assigned + timedelta(days=random.randint(1, 16))
            completed = completed.isoformat()

        add_task(
            {
                "task_id": f"TASK-{i + 1:03d}",
                "task": f"Sample task {i + 1}",
                "team": random.choice(TEAMS),
                "owner": random.choice(OWNERS),
                "priority": random.choice(PRIORITIES),
                "status": status,
                "assigned_date": assigned.isoformat(),
                "due_date": due.isoformat(),
                "completed_date": completed,
            }
        )


if __name__ == "__main__":
    seed_tasks(100)
    print("Seeded 100 sample tasks.")
