"""
Timer for your tasks
"""

import toga
import asyncio
from healthytimer.scheduler import Scheduler
from toga.style.pack import COLUMN, ROW


class Healthytimer(toga.App):
    def startup(self):
        self.scheduler = Scheduler(notify_callback=self.show_notification)
        main_box = toga.Box()

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

        self.task_input = toga.TextInput(placeholder='О чём напомнить?')
        self.time_input = toga.TextInput(placeholder='Время в минутах')
        self.add_remind = toga.Button(
            'Добавить напоминание',
            on_press=self.add_reminder
        )

        main_box.add(self.task_input)
        main_box.add(self.time_input)
        main_box.add(self.add_remind)

    def add_reminder(self, widget):
        print("button pressed")
        print(self.task_input.value)
        self.scheduler.add_task(
            name=self.task_input.value,
            interval_time=float(self.time_input.value)
        )

    def show_notification(self, name):
        async def _show():
            await self.main_window.dialog(toga.InfoDialog('Напоминание', name))
        asyncio.run_coroutine_threadsafe(_show(), self.loop)


def main():
    return Healthytimer()
