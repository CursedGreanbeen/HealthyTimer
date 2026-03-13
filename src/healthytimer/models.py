from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TimeUnit(Enum):
    MINUTES = 1
    HOURS = 2
    DAYS = 3
    WEEKS = 4

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
