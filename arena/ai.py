"""Autonomous AI responsible for making decisions for combatants."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import constants


@dataclass
class AutonomousAI:
    """Baseline AI prioritising survival and damage.

    The heuristics are deliberately simple yet illustrative. They examine
    the battlefield context to decide whether to heal, buff or attack.
    More elaborate behaviours can be implemented by subclassing or by
    injecting decision policies through data.
    """

    owner: "Combatant"

    def choose_action(self, context: "BattleContext") -> "SkillAction":
        from .actions import SkillAction

        available = self.owner.available_skills()
        if not available:
            raise RuntimeError(f"{self.owner.name} has no skills to use")

        # Try to heal if allies are low.
        heal_skills = [skill for skill in available if "heal" in skill.name.lower()]
        ally = context.pick_ally_to_heal(self.owner)
        if ally and ally.hp / ally.dynamic_stats.get("hp") < 0.4 and heal_skills:
            return SkillAction(self.owner, heal_skills[0])

        # Buff if starting fight.
        buff_skills = [skill for skill in available if "buff" in skill.name.lower()]
        if buff_skills and context.turn_number < 3:
            return SkillAction(self.owner, buff_skills[0])

        # Otherwise pick the skill with the highest power attribute.
        damaging = [skill for skill in available if hasattr(skill, "power")]
        if damaging:
            damaging.sort(key=lambda sk: getattr(sk, "power", 1.0), reverse=True)
            return SkillAction(self.owner, damaging[0])

        return SkillAction(self.owner, available[0])


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .actions import SkillAction
    from .battle import BattleContext
    from .combatant import Combatant
