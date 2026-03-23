from healthytimer.models import Task, Routine, TimeUnit, Importance


class Rearranger:
    def __init__(self, notify_callback, week):
        self.week = week
        self._notify_callback = notify_callback

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
        def sort_key(t):
            interval = 0
            if isinstance(t, Routine):
                interval = t.interval_in_seconds()
            return t.importance, interval, t.created_at

        days_tasks_shift = []
        for day in overloaded:
            flexible_tasks = list(filter(
                lambda t: t.is_flexible, self.week[day]
            ))
            flexible_tasks.sort(key=sort_key)
            day_load = len(self.week[day])
            tasks_to_shift = flexible_tasks[:(day_load - max_per_day)]
            for task in tasks_to_shift:
                days_tasks_shift.append((task, day))
        return days_tasks_shift

    def rearrange(self, days_tasks_shift, light, max_per_day) -> list:
        moved_tasks = []
        light.sort()

        for task, day in days_tasks_shift:
            if len(light) != 0:
                if task.importance == Importance.HIGH:
                    l_day = light[0]
                elif task.importance == Importance.LOW:
                    l_day = light[-1]
                else:
                    l_day = light[len(light) // 2]

                new_date = l_day
                light = [l_day for l_day in light if len(self.week[l_day]) < max_per_day]
            else:
                week_sorted_dates = sorted(self.week.keys())
                new_date = week_sorted_dates[-1]
                self._notify_callback(new_date)

            task.due_date = new_date
            moved_tasks.append(task)
            self.week[new_date].append(task)
            self.week[day].remove(task)

        return moved_tasks

    def new_task(self, task, max_per_day):
        date = task.due_date
        if date in self.week:
            self.week[date].append(task)
            overloaded, light = self.define_week_load(max_per_day)
            days_tasks_shift = self.sort_tasks(overloaded, max_per_day)
            moved_tasks = self.rearrange(days_tasks_shift, light, max_per_day)
            return moved_tasks
        return []
