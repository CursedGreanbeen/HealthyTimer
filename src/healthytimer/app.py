"""
Timer for your tasks
"""

import toga
import asyncio
import os
from healthytimer.scheduler import Scheduler
from healthytimer.storage import Storage
from healthytimer.models import Task, Routine, SingleTime, TimeUnit, Importance
from datetime import datetime, timedelta
from toga.style.pack import COLUMN, ROW


class Healthytimer(toga.App):
    def startup(self):
        db_path = os.path.join(os.path.dirname(__file__), "tasks.db")
        self.storage = Storage(db_path)
        self.scheduler = Scheduler(notify_callback=self.show_notification)

        self.start_box = toga.Box()
        self.routine_box = toga.Box()
        self.single_time_box = toga.Box()

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.start_box
        self.main_window.show()

        self.max_per_day_input = toga.TextInput(placeholder='Max tasks per day')
        self.new_routine = toga.Button(
            'New routine',
            on_press=self.choose_routine
        )
        self.new_single_time = toga.Button(
            'New single-time task',
            on_press=self.choose_single_time
        )

        self.start_box.add(self.max_per_day_input)
        self.start_box.add(self.new_routine)
        self.start_box.add(self.new_single_time)

    # ROUTINES
    def choose_routine(self, widget):
        self.main_window.content = self.routine_box

        self.routine_input = toga.TextInput(placeholder='task text')
        self.routine_interval_time_input = toga.TextInput(placeholder='time interval')
        self.routine_unit_input = toga.Selection(items=['minutes', 'hours', 'days', 'weeks'])
        self.routine_importance_input = toga.Selection(items=['low', 'medium', 'high'])
        self.routine_is_flexible_input = toga.Switch(text="Is it rearrangable?")
        self.routine_add_remind = toga.Button(
            'Add reminder',
            on_press=self.add_routine
        )

        self.routine_box.add(self.routine_input)
        self.routine_box.add(self.routine_interval_time_input)
        self.routine_box.add(self.routine_unit_input)
        self.routine_box.add(self.routine_importance_input)
        self.routine_box.add(self.routine_is_flexible_input)
        self.routine_box.add(self.routine_add_remind)

    # SINGLE-TIME TASKS
    def choose_single_time(self, widget):
        self.main_window.content = self.single_time_box

        self.single_time_input = toga.TextInput(placeholder='task text')
        self.single_time_deadline_input = toga.TextInput(placeholder='deadline')
        self.single_time_importance_input = toga.Selection(items=['low', 'medium', 'high'])
        self.single_time_is_flexible_input = toga.Switch(text="Is it rearrangable?")
        self.single_time_add_remind = toga.Button(
            'Add reminder',
            on_press=self.add_single_time
        )

        self.single_time_box.add(self.single_time_input)
        self.single_time_box.add(self.single_time_deadline_input)
        self.single_time_box.add(self.single_time_importance_input)
        self.single_time_box.add(self.single_time_is_flexible_input)
        self.single_time_box.add(self.single_time_add_remind)

    def add_routine(self, widget):
        print("button pressed")
        print(self.routine_input.value)

        importance_map = {
            'low': Importance.LOW,
            'medium': Importance.MEDIUM,
            'high': Importance.HIGH
        }
        unit_map = {
            'minutes': TimeUnit.MINUTES,
            'hours': TimeUnit.HOURS,
            'days': TimeUnit.DAYS,
            'weeks': TimeUnit.WEEKS
        }
        unit = unit_map[self.routine_unit_input.value]
        routine = Routine(
            name=self.routine_input.value,
            interval_time=float(self.routine_interval_time_input.value),
            unit=unit,
            importance=importance_map[self.routine_importance_input.value],
            is_flexible=self.routine_is_flexible_input.value,
            next_due=datetime.now() + timedelta(seconds=float(self.routine_interval_time_input.value) * unit.to_seconds())
        )
        routine = self.storage.insert_routine(routine)
        self.scheduler.add_task(routine)
        # self.rearranger.add_task(routine)
        self.main_window.content = self.start_box

    def add_single_time(self, widget):
        print("button pressed")
        print(self.single_time_input.value)

        importance_map = {
            'low': Importance.LOW,
            'medium': Importance.MEDIUM,
            'high': Importance.HIGH
        }

        deadline = self.single_time_deadline_input.value

        single_time = SingleTime(
            name=self.single_time_input.value,
            importance=importance_map[self.single_time_importance_input.value],
            is_flexible=self.single_time_is_flexible_input.value,
            due_date=datetime.deadline
        )

        single_time = self.storage.insert_single_time(single_time)
        # self.rearranger.add_task(single_time)
        self.main_window.content = self.start_box

    def show_notification(self, name):
        async def _show():
            await self.main_window.dialog(toga.InfoDialog('Напоминание', name))
        asyncio.run_coroutine_threadsafe(_show(), self.loop)


def main():
    return Healthytimer()
