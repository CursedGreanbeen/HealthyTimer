import sqlite3
from healthytimer.models import Task


class Storage:
    def __init__(self, db_path: str = 'tasks.db'):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                interval_time REAL,
                importance INTEGER
            ) 
        """)
        self.conn.commit()

    def insert_task(self, task: Task) -> Task:
        cursor = self.conn.execute(
            "INSERT INTO tasks (name, interval_time, importance) VALUES (?, ?, ?)",
            (task.name, task.interval_time, task.importance)
        )
        self.conn.commit()
        task.id = cursor.lastrowid
        return task

    def get_all_tasks(self) -> list[Task]:
        rows = self.conn.execute("SELECT * FROM tasks").fetchall()
        return [
            Task(
                id=row["id"],
                name=row["name"],
                interval_time=row["interval_time"],
                importance=row["importance"]
            )
            for row in rows
        ]

