import time
from threading import Thread


class Scheduler:
    def add_task(self, name, interval_time):
        thread = Thread(target=self._run, args=(name, interval_time))
        thread.start()

    def _run(self, name, interval_time):
        while True:
            time.sleep(interval_time * 60)
            self._notify(name)

    def _notify(self, name):
        self.notify_callback(name)
