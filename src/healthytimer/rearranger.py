from healthytimer.models import Task, Routine, TimeUnit, Importance


class Rearrangeer:
    def __init__(self, week):
        self.week = week

    def define_week_load(self, max_per_day):
        overloaded, light = [], []
        for day, tasks in self.week.items():
            day_load = len(tasks)
            if day_load > max_per_day:
                overloaded.append(day)
            elif day_load < max_per_day:
                light.append(day)
        return overloaded, light

    def sort_tasks(self, overloaded, max_per_day) -> list:
        result = []
        for day in overloaded:
            flexible_tasks = list(filter(
                lambda t: t.is_flexible, self.week[day]
            ))
            flexible_tasks.sort(key=lambda x: (
                x.importance, x.interval_time, x.created_at
            ))
            day_load = len(self.week[day])
            tasks_to_shift = flexible_tasks[:(day_load - max_per_day)]
            for task in tasks_to_shift:
                result.append((task, day))
        return result

    def rearrange(self, overloaded, light) -> list:
        pass
        task.due_date = new_date

    def new_task(self, task, max_per_day):
        return task