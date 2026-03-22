"""
Timer for your tasks
"""

import toga
import asyncio
import os
from datetime import time, datetime, timedelta
from healthytimer.scheduler import Scheduler
from healthytimer.storage import Storage
from healthytimer.models import Task, Routine, TimeUnit, Importance
from healthytimer.rearranger import Rearrangeer
from toga.style.pack import COLUMN, ROW, Pack


class Healthytimer(toga.App):
    def startup(self):
        db_path = os.path.join(os.path.dirname(__file__), "tasks.db")
        self.storage = Storage(db_path)
        self.scheduler = Scheduler(
            notify_callback=self.show_notification,
            storage=self.storage
        )
        self.rearranger = Rearranger()
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
        self.view_tasks = toga.Button(
            'View tasks',
            on_press=self.choose_view_tasks
        )

        self.start_box.add(self.max_per_day_input)
        self.start_box.add(self.new_routine)
        self.start_box.add(self.new_single_time)
        self.start_box.add(self.view_tasks)

        # ROUTINES
        self.routine_back_to_main = toga.Button(
            'Home',
            on_press=self.home
        )
        self.routine_input = toga.TextInput(placeholder='task text')
        self.routine_interval_time_input = toga.TextInput(placeholder='time interval')
        self.routine_unit_input = toga.Selection(items=['minutes', 'hours', 'days', 'weeks'])
        self.routine_importance_input = toga.Selection(items=['low', 'medium', 'high'])
        self.routine_is_flexible_input = toga.Switch(text="Is it rearrangable?")
        self.routine_add_remind = toga.Button(
            'Add reminder',
            on_press=self.submit_routine
        )
        self.routine_box.add(self.routine_back_to_main)
        self.routine_box.add(self.routine_input)
        self.routine_box.add(self.routine_interval_time_input)
        self.routine_box.add(self.routine_unit_input)
        self.routine_box.add(self.routine_importance_input)
        self.routine_box.add(self.routine_is_flexible_input)
        self.routine_box.add(self.routine_add_remind)

        # SINGLE-TIME TASKS
        self.single_time_back_to_main = toga.Button(
            'Home',
            on_press=self.home
        )
        self.single_time_input = toga.TextInput(placeholder='task text')
        self.single_time_deadline_input = toga.DateInput()
        self.single_time_importance_input = toga.Selection(items=['low', 'medium', 'high'])
        self.single_time_is_flexible_input = toga.Switch(text="Is it rearrangable?")
        self.single_time_add_remind = toga.Button(
            'Add reminder',
            on_press=self.submit_single_time
        )
        self.single_time_box.add(self.single_time_back_to_main)
        self.single_time_box.add(self.single_time_input)
        self.single_time_box.add(self.single_time_deadline_input)
        self.single_time_box.add(self.single_time_importance_input)
        self.single_time_box.add(self.single_time_is_flexible_input)
        self.single_time_box.add(self.single_time_add_remind)

        self.editing_task = None

    def choose_routine(self, widget):
        self.editing_task = None
        self.main_window.content = self.routine_box

    def choose_single_time(self, widget):
        self.editing_task = None
        self.main_window.content = self.single_time_box

    def choose_view_tasks(self, widget):
        self.view_tasks_box = toga.Box(style=Pack(direction=COLUMN))

        data = []

        for task in self.storage.get_all_tasks():
            task_data = (task.id, task.name, task.due_date)
            data.append(task_data)

        self.tasks_table = toga.Table(
            headings=['ID', 'Task', 'Due date'],
            data=data,
            on_select=self.on_task_select
        )

        self.table_back_to_main = toga.Button(
            'Home',
            on_press=self.home
        )
        self.edit_table_task = toga.Button(
            'Edit',
            on_press=self.edit_selected_task
        )
        self.delete_table_task = toga.Button(
            'Delete',
            on_press=self.delete_selected_task
        )

        self.view_tasks_box.add(self.tasks_table)
        self.view_tasks_box.add(self.table_back_to_main)
        self.view_tasks_box.add(self.edit_table_task)
        self.view_tasks_box.add(self.delete_table_task)
        self.main_window.content = self.view_tasks_box

    def home(self, widget):
        self.main_window.content = self.start_box

    def _create_routine(self, widget):
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
            due_date=datetime.now() + timedelta(
                seconds=float(self.routine_interval_time_input.value) * unit.to_seconds()
            )
        )
        routine = self.storage.insert_routine(routine)
        self.rearranger.add_task(routine)
        self.scheduler.add_task(routine)
        self.main_window.content = self.start_box

    def _create_single_time(self, widget):
        print("button pressed")
        print(self.single_time_input.value)

        importance_map = {
            'low': Importance.LOW,
            'medium': Importance.MEDIUM,
            'high': Importance.HIGH
        }

        single_time = Task(
            name=self.single_time_input.value,
            importance=importance_map[self.single_time_importance_input.value],
            is_flexible=self.single_time_is_flexible_input.value,
            due_date=datetime.combine(self.single_time_deadline_input.value, time(0, 0, 0))
        )

        single_time = self.storage.insert_single_time(single_time)
        self.rearranger.add_task(single_time)
        self.scheduler.add_task(single_time)
        self.main_window.content = self.start_box

    def submit_routine(self, widget):
        if self.editing_task:
            self._update_routine()
        else:
            self._create_routine(widget)

    def submit_single_time(self, widget):
        if self.editing_task:
            self._update_single_time()
        else:
            self._create_single_time(widget)

    def on_task_select(self, widget):
        row = widget.selection
        if row is None:
            return
        task_id = row.id  # the first column value
        self.selected_task = self.storage.find_task(task_id)

    def edit_selected_task(self, widget):
        if not hasattr(self, 'selected_task'):
            return
        self.editing_task = self.selected_task

        if isinstance(self.selected_task, Routine):
            unit_map = {TimeUnit.MINUTES: 'minutes', TimeUnit.HOURS: 'hours',
                        TimeUnit.DAYS: 'days', TimeUnit.WEEKS: 'weeks'}
            importance_map = {Importance.LOW: 'low', Importance.MEDIUM: 'medium', Importance.HIGH: 'high'}
            self.routine_input.value = self.selected_task.name
            self.routine_interval_time_input.value = str(self.selected_task.interval_time)
            self.routine_unit_input.value = unit_map[self.selected_task.unit]
            self.routine_importance_input.value = importance_map[self.selected_task.importance]
            self.routine_is_flexible_input.value = self.selected_task.is_flexible
            self.main_window.content = self.routine_box
        else:
            importance_map = {Importance.LOW: 'low', Importance.MEDIUM: 'medium', Importance.HIGH: 'high'}
            self.single_time_input.value = self.selected_task.name
            self.single_time_deadline_input.value = self.selected_task.due_date.date()
            self.single_time_importance_input.value = importance_map[self.selected_task.importance]
            self.single_time_is_flexible_input.value = self.selected_task.is_flexible
            self.main_window.content = self.single_time_box

    def _update_single_time(self):
        importance_map = {'low': Importance.LOW, 'medium': Importance.MEDIUM, 'high': Importance.HIGH}
        task = self.editing_task
        task.name = self.single_time_input.value
        task.importance = importance_map[self.single_time_importance_input.value]
        task.is_flexible = self.single_time_is_flexible_input.value
        task.due_date = datetime.combine(self.single_time_deadline_input.value, time(0, 0, 0))
        self.storage.update_routine(task)  # reuses the due_date update query
        self.scheduler.cancel_task(task.id)
        self.scheduler.add_task(task)
        self.editing_task = None
        self.main_window.content = self.view_tasks_box

    def _update_routine(self):
        importance_map = {'low': Importance.LOW, 'medium': Importance.MEDIUM, 'high': Importance.HIGH}
        unit_map = {'minutes': TimeUnit.MINUTES, 'hours': TimeUnit.HOURS,
                    'days': TimeUnit.DAYS, 'weeks': TimeUnit.WEEKS}
        task = self.editing_task
        task.name = self.routine_input.value
        task.interval_time = float(self.routine_interval_time_input.value)
        task.unit = unit_map[self.routine_unit_input.value]
        task.importance = importance_map[self.routine_importance_input.value]
        task.is_flexible = self.routine_is_flexible_input.value
        task.due_date = datetime.now() + timedelta(
            seconds=task.interval_time * task.unit.to_seconds()
        )
        self.storage.update_routine(task)
        self.scheduler.cancel_task(task.id)
        self.scheduler.add_task(task)
        self.editing_task = None
        self.main_window.content = self.view_tasks_box

    def delete_selected_task(self, widget):
        if not hasattr(self, 'selected_task'):
            return
        self.storage.delete_task(self.selected_task)
        self.scheduler.cancel_task(self.selected_task.id)
        self.choose_view_tasks(widget)

    def show_notification(self, name):
        async def _show():
            await self.main_window.dialog(toga.InfoDialog('Напоминание', name))
        asyncio.run_coroutine_threadsafe(_show(), self.loop)


def main():
    return Healthytimer()
