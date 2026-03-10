import sqlite3
from healthytimer.models import Task, Routine, TimeUnit, Importance
from datetime import datetime
import os


class Storage:
    def __init__(self, db_path: str = 'tasks.db'):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                task_type TEXT,
                name TEXT NOT NULL,
                importance INTEGER,
                is_flexible BOOL,
                interval_time REAL,
                unit INTEGER,
                due_date TEXT
            ) 
        """)
        self.conn.commit()

    def insert_routine(self, routine: Routine) -> Routine:
        cursor = self.conn.execute(
            "INSERT INTO tasks "
            "(task_type, name, importance, is_flexible, created_at, interval_time, unit, due_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                'routine',
                routine.name,
                routine.importance.value,
                routine.is_flexible,
                routine.created_at.isoformat(),
                routine.interval_time,
                routine.unit.value,
                routine.due_date.isoformat(),
            )
        )
        self.conn.commit()
        routine.id = cursor.lastrowid
        return routine

    def insert_single_time(self, singletime: Task) -> Task:
        cursor = self.conn.execute(
            "INSERT INTO tasks "
            "(task_type, name, importance, is_flexible, created_at, due_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                'single_time',
                singletime.name,
                singletime.importance.value,
                singletime.is_flexible,
                singletime.created_at.isoformat(),
                singletime.due_date.isoformat()
            )
        )
        self.conn.commit()
        singletime.id = cursor.lastrowid
        return singletime

    def update_routine(self, routine):
        cursor = self.conn.execute(f"UPDATE tasks SET due_date = ? WHERE id = ?",
                                   (routine.due_date, routine.id,))
        self.conn.commit()

    def delete_task(self, task):
        cursor = self.conn.execute(f"DELETE from tasks WHERE id = ?", (task.id,))
        self.conn.commit()

    def get_all_tasks(self) -> list[Task]:
        tasks = []
        rows = self.conn.execute("SELECT * FROM tasks").fetchall()
        for row in rows:
            if row["task_type"] == 'routine':
                tasks.append(
                    Routine(
                        id=row["id"],
                        name=row["name"],
                        importance=Importance(row["importance"]),
                        is_flexible=row["is_flexible"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        interval_time=row["interval_time"],
                        unit=TimeUnit(row["unit"]),
                        due_date=datetime.fromisoformat(row["due_date"]),
                    )
                )
            else:
                tasks.append(
                    Task(
                        id=row["id"],
                        name=row["name"],
                        importance=Importance(row["importance"]),
                        is_flexible=row["is_flexible"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        due_date=datetime.fromisoformat(row["due_date"]),
                    )
                )
        return tasks
