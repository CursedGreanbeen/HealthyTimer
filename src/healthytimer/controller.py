from datetime import time, datetime, timedelta
from healthytimer.scheduler import Scheduler
from healthytimer.storage import Storage
from healthytimer.models import Task, Routine, TimeUnit, Importance
from healthytimer.rearranger import Rearranger


class TaskService:
    def __init__(self, storage, scheduler, rearranger):
        self.storage = storage
        self.scheduler = scheduler
        self.rearranger = rearranger

    def collect_week(self, user_id):
        week_window = datetime.now() + timedelta(days=7)
        week = {(datetime.now() + timedelta(days=i)).date(): [] for i in range(8)}
        for task in self.storage.get_all_tasks(user_id):
            if datetime.now() <= task.due_date <= week_window:
                week[task.due_date.date()].append(task)
        return week

    def create_routine(self, user_id, name, interval_time, unit, importance, is_flexible, max_per_day):
        routine = Routine(
            user_id=user_id,
            name=name,
            interval_time=interval_time,
            unit=unit,
            importance=importance,
            is_flexible=is_flexible,
            due_date=datetime.now() + timedelta(seconds=interval_time * unit.to_seconds())
        )
        routine = self.storage.insert_routine(routine)
        self.rearranger.week = self.collect_week(user_id)
        moved_tasks = self.rearranger.new_task(routine, max_per_day)
        for task in moved_tasks:
            self.storage.update_task(task)
        self.scheduler.add_task(routine)

    def create_single_time(self, user_id, name, importance, is_flexible, date, max_per_day):
        single_time = Task(
            user_id=user_id,
            name=name,
            importance=importance,
            is_flexible=is_flexible,
            due_date=datetime.combine(date, time(0, 0, 0))
        )
        single_time = self.storage.insert_single_time(single_time)
        self.rearranger.week = self.collect_week(user_id)
        moved_tasks = self.rearranger.new_task(single_time, max_per_day)
        for task in moved_tasks:
            self.storage.update_task(task)
        self.scheduler.add_task(single_time)

    def update_routine(self, task, name, interval_time, unit, importance, is_flexible):
        task.name = name
        task.interval_time = interval_time
        task.unit = unit
        task.importance = importance
        task.is_flexible = is_flexible
        task.due_date = datetime.now() + timedelta(seconds=task.interval_in_seconds())
        self.storage.update_task(task)
        self.scheduler.cancel_task(task.id)
        self.scheduler.add_task(task)

    def update_single_time(self, task, name, importance, is_flexible, date):
        task.name = name
        task.importance = importance
        task.is_flexible = is_flexible
        task.due_date = datetime.combine(date, time(0, 0, 0))
        self.storage.update_task(task)
        self.scheduler.cancel_task(task.id)
        self.scheduler.add_task(task)

    def delete_task(self, task):
        self.storage.delete_task(task)
        self.scheduler.cancel_task(task.id)
