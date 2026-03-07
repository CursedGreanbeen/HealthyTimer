from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Task:
    name: str
    interval_time: float
    importance: int          # 1 = low, 2 = medium, 3 = high
    id: int = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)
