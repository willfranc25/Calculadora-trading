"""Speed based action timeline similar to ATB gauges."""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import List


@dataclass(order=True)
class TimelineEntry:
    """Represents a combatant scheduled to act."""

    ready_at: float
    counter: int
    combatant: "Combatant" = field(compare=False)


class Timeline:
    """Manages initiative order based on speed."""

    def __init__(self) -> None:
        self.queue: List[TimelineEntry] = []
        self.counter = 0

    def add_combatant(self, combatant: "Combatant", *, current_time: float = 0.0) -> None:
        speed = combatant.dynamic_stats.get("speed")
        ready_at = current_time + max(1.0, 100.0 / max(speed, 1.0))
        heapq.heappush(self.queue, TimelineEntry(ready_at, self.counter, combatant))
        self.counter += 1

    def pop_next(self) -> tuple[float, "Combatant"]:
        entry = heapq.heappop(self.queue)
        return entry.ready_at, entry.combatant

    def schedule_next(self, combatant: "Combatant", *, current_time: float) -> None:
        self.add_combatant(combatant, current_time=current_time)

    def is_empty(self) -> bool:
        return not self.queue


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .combatant import Combatant
