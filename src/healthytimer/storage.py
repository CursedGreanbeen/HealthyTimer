import sqlite3
from healthytimer.models import Task, Routine, TimeUnit, Importance
from datetime import datetime
import os


class Storage:
    def __init__(self, db_path: str = 'tasks.db'):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
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
        conn.commit()
        conn.close()

    def insert_routine(self, routine: Routine) -> Routine:
        conn = self._get_conn()
        cursor = conn.execute(
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
        conn.commit()
        routine.id = cursor.lastrowid
        conn.close()
        return routine

    def insert_single_time(self, singletime: Task) -> Task:
        conn = self._get_conn()
        cursor = conn.execute(
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
        conn.commit()
        singletime.id = cursor.lastrowid
        conn.close()
        return singletime

    def update_task(self, task):
        conn = self._get_conn()
        conn.execute(f"UPDATE tasks SET due_date = ? WHERE id = ?",
                                   (task.due_date.isoformat(), task.id,))
        conn.commit()
        conn.close()

    def delete_task(self, task):
        conn = self._get_conn()
        conn.execute(f"DELETE from tasks WHERE id = ?", (task.id,))
        conn.commit()
        conn.close()

    def get_all_tasks(self) -> list[Task]:
        conn = self._get_conn()
        tasks = []
        rows = conn.execute("SELECT * FROM tasks").fetchall()
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
        conn.close()
        return tasks

    def find_task(self, id):
        conn = self._get_conn()
        row = conn.execute(f"SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
        if row["task_type"] == 'routine':
            task = Routine(
                    id=row["id"],
                    name=row["name"],
                    importance=Importance(row["importance"]),
                    is_flexible=row["is_flexible"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    interval_time=row["interval_time"],
                    unit=TimeUnit(row["unit"]),
                    due_date=datetime.fromisoformat(row["due_date"]),
                )
        else:
            task = Task(
                    id=row["id"],
                    name=row["name"],
                    importance=Importance(row["importance"]),
                    is_flexible=row["is_flexible"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    due_date=datetime.fromisoformat(row["due_date"]),
                )
        conn.close()
        return task
