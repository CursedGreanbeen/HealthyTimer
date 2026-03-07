"""
Timer for your tasks
"""

import toga
import asyncio
from healthytimer.scheduler import Scheduler
from healthytimer.storage import Storage
from healthytimer.models import Task
from toga.style.pack import COLUMN, ROW


class Healthytimer(toga.App):
    def startup(self):
        self.storage = Storage("tasks.db")
        self.scheduler = Scheduler(notify_callback=self.show_notification)
        main_box = toga.Box()

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

        self.task_input = toga.TextInput(placeholder='О чём напомнить?')
        self.time_input = toga.TextInput(placeholder='Время в минутах')
        self.importance_input = toga.Selection(items=[1, 2, 3])
        self.add_remind = toga.Button(
            'Добавить напоминание',
            on_press=self.add_reminder
        )

        main_box.add(self.task_input)
        main_box.add(self.time_input)
        main_box.add(self.importance_input)
        main_box.add(self.add_remind)

    def add_reminder(self, widget):
        print("button pressed")
        print(self.task_input.value)
        task = Task(
            name=self.task_input.value,
            interval_time=float(self.time_input.value),
            importance=int(self.importance_input.value)
        )
        task = self.storage.insert_task(task)
        self.scheduler.add_task(task)

    def show_notification(self, name):
        async def _show():
            await self.main_window.dialog(toga.InfoDialog('Напоминание', name))
        asyncio.run_coroutine_threadsafe(_show(), self.loop)


def main():
    return Healthytimer()
