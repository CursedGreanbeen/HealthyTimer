import time
from threading import Thread
import threading
from healthytimer.models import Task, TimeUnit, Importance


class Scheduler:
    def __init__(self, notify_callback):
        self._notify_callback = notify_callback
        self._stop_event = threading.Event()

    def add_task(self, task: Task):
        thread = Thread(target=self._run,
                        args=(task.name, task.interval_time, task.importance, task.unit),
                        daemon=True)
        thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self, name, interval_time, importance, unit):
        while not self._stop_event.is_set():
            time.sleep(interval_time * TimeUnit.to_seconds(unit))
            if not self._stop_event.is_set():
                self._notify_callback(name)
