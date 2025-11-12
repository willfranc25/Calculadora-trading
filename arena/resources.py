"""Resource system allowing characters to use custom meters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional

from . import constants
from .events import EventManager


@dataclass
class Resource:
    """Configuration of an individual resource bar."""

    name: str
    maximum: float
    value: float
    regen_per_turn: float = 0.0
    decay_per_turn: float = 0.0
    allow_overcap: bool = False
    gain_on_events: Mapping[str, float] = None

    def clamp(self) -> None:
        if self.allow_overcap:
            return
        self.value = max(0.0, min(self.value, self.maximum))


class ResourcePool:
    """Container managing multiple resources and hooks to events."""

    def __init__(
        self,
        resources: Mapping[str, Resource],
        manager: EventManager,
        *,
        owner: "Combatant",
    ) -> None:
        self.resources: Dict[str, Resource] = {name: res for name, res in resources.items()}
        self.manager = manager
        self.owner = owner
        for resource in self.resources.values():
            if resource.gain_on_events:
                for event_name, amount in resource.gain_on_events.items():
                    manager.register(event_name, self._make_gain_callback(resource, amount))

    def _make_gain_callback(self, resource: Resource, amount: float):
        def callback(context):
            resource.value += amount
            resource.clamp()
        return callback

    def can_pay(self, costs: Mapping[str, float]) -> bool:
        for name, cost in costs.items():
            resource = self.resources.get(name)
            if not resource or resource.value < cost:
                return False
        return True

    def pay(self, costs: Mapping[str, float]) -> None:
        for name, cost in costs.items():
            resource = self.resources.get(name)
            if not resource:
                continue
            resource.value -= cost
            resource.clamp()

    def on_turn_start(self) -> None:
        for resource in self.resources.values():
            resource.value += resource.regen_per_turn
            resource.value -= resource.decay_per_turn
            resource.clamp()

    def on_turn_end(self) -> None:
        pass

    def add(self, name: str, amount: float) -> None:
        resource = self.resources.get(name)
        if not resource:
            return
        resource.value += amount
        resource.clamp()

    def summary(self) -> Dict[str, float]:
        return {name: resource.value for name, resource in self.resources.items()}


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .combatant import Combatant
