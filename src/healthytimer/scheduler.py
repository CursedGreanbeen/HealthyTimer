import time
from datetime import datetime, timedelta
from threading import Thread
import threading
from healthytimer.models import Task, Routine, SingleTime, TimeUnit


class Scheduler:
    def __init__(self, notify_callback):
        self._notify_callback = notify_callback
        self._stop_event = threading.Event()

    def add_routine(self, routine: Routine):
        thread = Thread(target=self._run_routine,
                        args=(routine.name, routine.interval_time, routine.unit),
                        daemon=True)
        thread.start()

    def add_single_time(self, single_time: SingleTime):
        thread = Thread(target=self._run_single_time,
                        args=(single_time.name, single_time.due_date),
                        daemon=True)
        thread.start()

    def stop(self):
        self._stop_event.set()

    def _run_routine(self, name, interval_time, unit):
        while not self._stop_event.is_set():
            time.sleep(interval_time * TimeUnit.to_seconds(unit))
            if not self._stop_event.is_set():
                self._notify_callback(name)

    def _run_single_time(self, name, due_date):
        time.sleep((due_date - datetime.now()).total_seconds())
        if not self._stop_event.is_set():
            self._notify_callback(name)
