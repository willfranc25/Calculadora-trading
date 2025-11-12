"""Defines combat entities (players, summons, etc.)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from . import constants
from .effects import EffectController, EffectInstance
from .events import EventManager
from .resources import ResourcePool
from .stats import DynamicStats, Stats


@dataclass
class SkillReference:
    """Lightweight pointer to a skill by name."""

    name: str
    cooldown: int = 0
    tags: List[str] = field(default_factory=list)


class Combatant:
    """Base class for everything that can act during battle."""

    def __init__(
        self,
        name: str,
        stats: Stats,
        skills: Sequence["Skill"],
        *,
        tags: Optional[Sequence[str]] = None,
        resources: Optional[Dict[str, "Resource"]] = None,
        event_manager: Optional[EventManager] = None,
    ) -> None:
        self.name = name
        self.tags = list(tags or [])
        self.dynamic_stats = DynamicStats(stats)
        self.hp = self.dynamic_stats.get("hp")
        self.skills = list(skills)
        self.skill_cooldowns: Dict[str, int] = {skill.name: 0 for skill in skills}
        self.event_manager = event_manager or EventManager()
        self.effects = EffectController(self, self.dynamic_stats, self.event_manager)
        self.resource_pool = ResourcePool(resources or {}, self.event_manager, owner=self)
        self.alive = True
        self.team: Optional["Team"] = None
        self.ui_state: Dict[str, float] = {}

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    # --- Health ---------------------------------------------------------
    def apply_damage(self, amount: float, damage_type: str, *, source: Optional["Combatant"] = None,
                     is_critical: bool = False) -> float:
        if not self.alive:
            return 0.0
        mitigation = 1.0 - self.dynamic_stats.get_resistance(damage_type)
        mitigated = max(amount * mitigation, 0)
        self.hp -= mitigated
        self.event_manager.broadcast(
            constants.ON_RECEIVE_DAMAGE,
            source=self,
            data={
                constants.DMG_AMOUNT: mitigated,
                constants.DMG_TYPE: damage_type,
                constants.DMG_IS_CRIT: is_critical,
                "attacker": source.name if source else None,
            },
        )
        if self.hp <= 0:
            self.die()
        return mitigated

    def heal(self, amount: float, *, source: Optional["Combatant"] = None) -> float:
        if not self.alive or amount <= 0:
            return 0.0
        missing = self.dynamic_stats.get("hp") - self.hp
        healed = min(amount, missing)
        self.hp += healed
        self.event_manager.broadcast(
            constants.ON_HEALED,
            source=self,
            data={"amount": healed, "healer": source.name if source else None},
        )
        return healed

    def die(self) -> None:
        if not self.alive:
            return
        self.alive = False
        self.event_manager.broadcast(constants.ON_EXIT_BATTLE, source=self)
        if self.team:
            self.team.handle_death(self)

    # --- Skills ---------------------------------------------------------
    def available_skills(self) -> List["Skill"]:
        return [
            skill
            for skill in self.skills
            if self.skill_cooldowns[skill.name] == 0 and self.resource_pool.can_pay(skill.costs)
        ]

    def start_cooldown(self, skill: "Skill") -> None:
        self.skill_cooldowns[skill.name] = skill.cooldown

    def reduce_cooldowns(self) -> None:
        for name in list(self.skill_cooldowns.keys()):
            if self.skill_cooldowns[name] > 0:
                self.skill_cooldowns[name] -= 1

    # --- Effects --------------------------------------------------------
    def apply_effect(self, effect: EffectInstance) -> None:
        self.effects.apply(effect)

    def remove_effect(self, name: str) -> None:
        self.effects.remove_effect(name)

    # --- Turn handling --------------------------------------------------
    def start_turn(self) -> None:
        self.reduce_cooldowns()
        self.effects.tick_all()
        self.resource_pool.on_turn_start()
        self.event_manager.broadcast(constants.ON_TURN_START, source=self)

    def end_turn(self) -> None:
        self.resource_pool.on_turn_end()
        self.event_manager.broadcast(constants.ON_TURN_END, source=self)

    # --- AI -------------------------------------------------------------
    def choose_action(self, context: "BattleContext") -> "SkillAction":
        from .ai import AutonomousAI

        ai = AutonomousAI(self)
        return ai.choose_action(context)

    def perform_action(self, action: "SkillAction", context: "BattleContext") -> None:
        action.execute(context)

    # --- UI -------------------------------------------------------------
    def snapshot(self) -> Dict[str, any]:
        """Collect info for UI overlays."""
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.dynamic_stats.get("hp"),
            "stats": self.dynamic_stats.as_dict(),
            "tags": list(self.tags),
            "effects": self.effects.summary(),
            "resources": self.resource_pool.summary(),
            "cooldowns": dict(self.skill_cooldowns),
        }


class Team:
    """Lightweight container used by :class:`Battle` to group combatants."""

    def __init__(self, name: str, members: Sequence[Combatant]):
        self.name = name
        self.members = list(members)
        for member in self.members:
            member.team = self

    def alive_members(self) -> List[Combatant]:
        return [member for member in self.members if member.alive]

    def handle_death(self, member: Combatant) -> None:
        for ally in self.alive_members():
            ally.event_manager.broadcast(constants.ON_ALLY_DEATH, source=member)
        if self.is_defeated:
            return

    @property
    def is_defeated(self) -> bool:
        return not any(member.alive for member in self.members)


# typing imports at bottom to avoid cycles
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .actions import SkillAction
    from .battle import BattleContext
    from .resources import Resource
    from .skills import Skill
