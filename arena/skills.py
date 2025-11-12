"""Definition of combat skills and passives."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

from . import constants
from .events import EventManager
from .stats import DynamicStats


@dataclass
class Skill:
    """Base class for skills.

    Skills can be configured in data and loaded dynamically. For the demo
    implementation we provide a set of canonical behaviours.
    """

    name: str
    cooldown: int = 0
    tags: Sequence[str] = field(default_factory=list)
    costs: Dict[str, float] = field(default_factory=dict)

    def select_targets(self, user: "Combatant", context: "BattleContext") -> List["Combatant"]:
        raise NotImplementedError

    def perform(self, user: "Combatant", targets: Sequence["Combatant"], context: "BattleContext") -> None:
        raise NotImplementedError

    def execute(self, user: "Combatant", context: "BattleContext") -> None:
        targets = self.select_targets(user, context)
        user.event_manager.broadcast(constants.ON_USE_SKILL, source=user, data={"skill": self.name})
        user.resource_pool.pay(self.costs)
        self.perform(user, targets, context)
        user.start_cooldown(self)


@dataclass
class SingleTargetAttack(Skill):
    """Simple damaging ability used for the base AI."""

    power: float = 1.0
    damage_type: str = "physical"

    def select_targets(self, user: "Combatant", context: "BattleContext") -> List["Combatant"]:
        return [context.pick_enemy_target(user)]

    def perform(self, user: "Combatant", targets: Sequence["Combatant"], context: "BattleContext") -> None:
        for target in targets:
            if not target:
                continue
            damage, is_crit = context.compute_damage(user, target, self.power, self.damage_type, self.tags)
            target.apply_damage(damage, self.damage_type, source=user, is_critical=is_crit)
            user.event_manager.broadcast(
                constants.ON_ATTACK,
                source=user,
                targets=[target],
                data={constants.DMG_AMOUNT: damage, constants.DMG_TYPE: self.damage_type},
            )


@dataclass
class HealingSkill(Skill):
    """Heals the lowest HP ally."""

    amount: float = 50.0

    def select_targets(self, user: "Combatant", context: "BattleContext") -> List["Combatant"]:
        return [context.pick_ally_to_heal(user)]

    def perform(self, user: "Combatant", targets: Sequence["Combatant"], context: "BattleContext") -> None:
        for target in targets:
            if target:
                healed = target.heal(self.amount, source=user)
                context.log_event(f"{user.name} cura a {target.name} por {healed:.0f} HP")


@dataclass
class BuffSkill(Skill):
    """Applies a stat modifier effect."""

    stat: str = "atk"
    amount: float = 20.0
    duration: int = 2

    def select_targets(self, user: "Combatant", context: "BattleContext") -> List["Combatant"]:
        return [user]

    def perform(self, user: "Combatant", targets: Sequence["Combatant"], context: "BattleContext") -> None:
        from .effects import EffectInstance

        for target in targets:
            effect = EffectInstance(
                name=f"buff_{self.stat}",
                duration=self.duration,
                modifiers={self.stat: self.amount},
            )
            target.apply_effect(effect)
            context.log_event(f"{user.name} potencia {self.stat} de {target.name}")


# typing imports at bottom
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .battle import BattleContext
    from .combatant import Combatant
