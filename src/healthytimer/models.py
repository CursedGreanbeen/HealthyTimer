from dataclasses import dataclass, field
from datetime import datetime
from dateutil.relativedelta import relativedelta
from enum import Enum


class TimeUnit(Enum):
    MINUTES = 0
    HOURS = 1
    DAYS = 2
    WEEKS = 3
    MONTHS = 4
    YEARS = 5

    def calc_interval(self, interval):
        match self:
            case TimeUnit.MINUTES: return relativedelta(minutes=interval)
            case TimeUnit.HOURS: return relativedelta(hours=interval)
            case TimeUnit.DAYS: return relativedelta(days=interval)
            case TimeUnit.WEEKS: return relativedelta(weeks=interval)
            case TimeUnit.MONTHS: return relativedelta(months=interval)
            case TimeUnit.YEARS: return relativedelta(years=interval)


class Importance(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    user_id: int
    name: str
    importance: Importance
    is_flexible: bool
    due_date: datetime = field(default=None)
    id: int = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Routine(Task):
    interval_time: float = 0.0
    unit: TimeUnit = TimeUnit.DAYS
    # is_running = True

    # def interval_in_seconds(self) -> float:
    #     return self.interval_time * self.unit.to_seconds()
