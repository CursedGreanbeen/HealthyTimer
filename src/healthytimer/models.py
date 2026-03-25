from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TimeUnit(Enum):
    MINUTES = 0
    HOURS = 1
    DAYS = 2
    WEEKS = 3
    MONTHS = 4
    YEARS = 5

    def to_seconds(self) -> float:
        conversions = {
            TimeUnit.MINUTES: 60,
            TimeUnit.HOURS:   60 * 60,
            TimeUnit.DAYS:    60 * 60 * 24,
            TimeUnit.WEEKS:   60 * 60 * 24 * 7,
        }
        return conversions[self]


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

    def interval_in_seconds(self) -> float:
        return self.interval_time * self.unit.to_seconds()
