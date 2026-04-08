import time
from datetime import datetime, timedelta
from threading import Thread
import threading
from healthytimer.models import Task, Routine, TimeUnit


class Scheduler:
    def __init__(self, notifier, storage):
        self.notifier = notifier
        self._storage = storage
        self._tasks = {}  # id -> task
        self._wakeup = threading.Event()
        thread = Thread(target=self._loop, daemon=True)
        thread.start()

    def add_task(self, task):
        self._tasks[task.id] = task
        self._wakeup.set()  # interrupt sleep, recalculate

    def cancel_task(self, task_id):
        self._tasks.pop(task_id, None)
        self._wakeup.set()

    def _loop(self):
        while True:
            self._wakeup.clear()
            next_task, seconds = self._find_next()
            self._wakeup.wait(timeout=seconds)

            if next_task and (next_task.due_date <= datetime.now()):
                self.notifier.notify_task(next_task)
                if isinstance(next_task, Routine):
                    next_task.due_date = datetime.now() + next_task.unit.calc_interval(next_task.interval_time)
                    self._storage.update_task(next_task)
                else:
                    self._tasks.pop(next_task.id)
                    self._storage.delete_task(next_task)

    def _find_next(self):
        now = datetime.now()
        upcoming = [(task, task.due_date) for task in self._tasks.values()]
        if not upcoming:
            return None, 99999
        next_task, due = min(upcoming, key=lambda x: x[1])
        seconds = (due - now).total_seconds()
        return next_task, max(0, seconds)
