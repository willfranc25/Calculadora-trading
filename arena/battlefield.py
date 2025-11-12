"""Battlefield and field effects implementation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import constants
from .events import EventManager


@dataclass
class FieldEffect:
    """Represents a global or side-specific battlefield modifier."""

    name: str
    duration: int
    tags: List[str] = field(default_factory=list)
    modifiers: Dict[str, float] = field(default_factory=dict)
    priority: int = 0

    def on_apply(self, manager: EventManager) -> None:
        manager.broadcast(constants.ON_FIELD_APPLY, data={"effect": self.name})

    def on_tick(self, manager: EventManager) -> None:
        manager.broadcast(constants.ON_FIELD_TICK, data={"effect": self.name})

    def on_expire(self, manager: EventManager) -> None:
        manager.broadcast(constants.ON_FIELD_EXPIRE, data={"effect": self.name})


class Battlefield:
    """Keeps track of field effects and provides queries for combat logic."""

    def __init__(self, manager: EventManager) -> None:
        self.manager = manager
        self.global_effects: List[FieldEffect] = []

    def add_effect(self, effect: FieldEffect) -> None:
        self.global_effects.append(effect)
        self.global_effects.sort(key=lambda eff: eff.priority, reverse=True)
        effect.on_apply(self.manager)

    def tick(self) -> None:
        for effect in list(self.global_effects):
            effect.on_tick(self.manager)
            effect.duration -= 1
            if effect.duration <= 0:
                effect.on_expire(self.manager)
                self.global_effects.remove(effect)

    def query_modifier(self, tag: str) -> float:
        """Return the cumulative modifier for a given tag."""
        return sum(effect.modifiers.get(tag, 0.0) for effect in self.global_effects)

    def snapshot(self) -> List[Dict[str, any]]:
        return [
            {"name": effect.name, "duration": effect.duration, "tags": effect.tags}
            for effect in self.global_effects
        ]
