"""Status effects and buff/debuff infrastructure."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import constants
from .events import EventContext, EventManager
from .stats import DynamicStats


@dataclass
class EffectInstance:
    """Represents an active status effect on a combatant."""

    name: str
    duration: int
    stacks: int = 1
    tags: List[str] = field(default_factory=list)
    modifiers: Dict[str, float] = field(default_factory=dict)
    on_tick: Optional[callable] = None
    on_expire: Optional[callable] = None

    def tick(self, holder: "Combatant", manager: EventManager) -> None:
        if self.on_tick:
            self.on_tick(holder, self, manager)
        self.duration -= 1
        if self.duration <= 0:
            self.expire(holder, manager)

    def expire(self, holder: "Combatant", manager: EventManager) -> None:
        if self.on_expire:
            self.on_expire(holder, self, manager)
        holder.remove_effect(self.name)


class EffectController:
    """Manages all effects for a combatant and updates stats accordingly."""

    def __init__(self, owner: "Combatant", stats: DynamicStats, manager: EventManager) -> None:
        self.owner = owner
        self.stats = stats
        self.manager = manager
        self.effects: Dict[str, EffectInstance] = {}

    def apply(self, effect: EffectInstance) -> None:
        existing = self.effects.get(effect.name)
        if existing:
            existing.stacks += effect.stacks
            existing.duration = max(existing.duration, effect.duration)
        else:
            self.effects[effect.name] = effect
        for stat, value in effect.modifiers.items():
            self.stats.apply_modifier(stat, value * effect.stacks)
        self.manager.broadcast(
            constants.ON_APPLY_EFFECT,
            source=self.owner,
            data={"effect": effect.name, "stacks": self.effects[effect.name].stacks},
        )

    def remove_effect(self, name: str) -> None:
        effect = self.effects.pop(name, None)
        if not effect:
            return
        for stat, value in effect.modifiers.items():
            self.stats.apply_modifier(stat, -value * effect.stacks)
        self.manager.broadcast(
            constants.ON_REMOVE_EFFECT,
            source=self.owner,
            data={"effect": name},
        )

    def tick_all(self) -> None:
        for effect in list(self.effects.values()):
            effect.tick(self.owner, self.manager)

    def summary(self) -> Dict[str, Dict[str, float]]:
        return {
            name: {
                "duration": effect.duration,
                "stacks": effect.stacks,
                **effect.modifiers,
            }
            for name, effect in self.effects.items()
        }


# circular import guard
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .combatant import Combatant
