"""Atomic battle actions executed by combatants."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SkillAction:
    """Executes a :class:`~arena.skills.Skill` for a combatant."""

    user: "Combatant"
    skill: "Skill"

    def execute(self, context: "BattleContext") -> None:
        if not self.user.alive:
            return
        context.log_event(f"{self.user.name} usa {self.skill.name}")
        self.skill.execute(self.user, context)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .battle import BattleContext
    from .combatant import Combatant
    from .skills import Skill
