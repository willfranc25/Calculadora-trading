"""High level orchestration of a battle."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from . import constants
from .actions import SkillAction
from .battlefield import Battlefield
from .combatant import Combatant, Team
from .events import EventManager
from .timeline import Timeline


@dataclass
class BattleContext:
    """Runtime object passed to skills and AI with battle-wide data."""

    battle: "Battle"

    @property
    def turn_number(self) -> int:
        return self.battle.turn_number

    def pick_enemy_target(self, requester: Combatant) -> Optional[Combatant]:
        enemies = self.battle.enemies_of(requester)
        alive = [c for c in enemies if c.alive]
        return random.choice(alive) if alive else None

    def pick_ally_to_heal(self, requester: Combatant) -> Optional[Combatant]:
        allies = self.battle.allies_of(requester)
        if not allies:
            return None
        return min(allies, key=lambda ally: ally.hp / max(ally.dynamic_stats.get("hp"), 1))

    def compute_damage(
        self,
        attacker: Combatant,
        defender: Combatant,
        power: float,
        damage_type: str,
        tags: List[str],
    ) -> tuple[float, bool]:
        base_stat = attacker.dynamic_stats.get("atk") if damage_type in {"physical", "true"} else attacker.dynamic_stats.get("mag")
        defense = defender.dynamic_stats.get("defense") if damage_type in {"physical"} else defender.dynamic_stats.get("resistance")
        mitigation = max(0.1, 100.0 / (100.0 + defense))
        damage = base_stat * power * mitigation
        modifier = 1.0 + self.battle.battlefield.query_modifier(damage_type)
        if tags:
            for tag in tags:
                if defender.has_tag(tag + "_weak"):
                    modifier += 0.25
                if defender.has_tag(tag + "_resist"):
                    modifier -= 0.25
        damage *= modifier
        crit_chance = attacker.dynamic_stats.get("crit_chance")
        is_crit = random.random() < crit_chance
        if is_crit:
            damage *= attacker.dynamic_stats.get("crit_damage")
        return damage, is_crit

    def allies_of(self, requester: Combatant) -> List[Combatant]:
        return self.battle.allies_of(requester)

    def enemies_of(self, requester: Combatant) -> List[Combatant]:
        return self.battle.enemies_of(requester)

    def log_event(self, message: str) -> None:
        self.battle.log(message)


class Battle:
    """Controls the lifecycle of a combat scenario."""

    def __init__(self, team_a: Team, team_b: Team, *, manager: Optional[EventManager] = None) -> None:
        self.manager = manager or EventManager()
        self.team_a = team_a
        self.team_b = team_b
        self.timeline = Timeline()
        self.turn_number = 0
        self.time = 0.0
        self.battlefield = Battlefield(self.manager)
        self.log_messages: List[str] = []

        for combatant in team_a.members + team_b.members:
            combatant.event_manager = self.manager
            combatant.resource_pool.manager = self.manager
            self.timeline.add_combatant(combatant)
            self.manager.broadcast(constants.ON_ENTER_BATTLE, source=combatant)

    def log(self, message: str) -> None:
        self.log_messages.append(message)

    # --- Queries --------------------------------------------------------
    def allies_of(self, requester: Combatant) -> List[Combatant]:
        team = requester.team
        if not team:
            return [requester]
        return team.alive_members()

    def enemies_of(self, requester: Combatant) -> List[Combatant]:
        team = requester.team
        if team is self.team_a:
            return self.team_b.alive_members()
        if team is self.team_b:
            return self.team_a.alive_members()
        # Summons might not belong to either team yet: fallback to all opponents.
        return [combatant for combatant in self.team_a.members + self.team_b.members if combatant.team is not team]

    def run(self, max_turns: int = 100) -> None:
        context = BattleContext(self)
        while self.turn_number < max_turns and not self.is_finished:
            current_time, combatant = self.timeline.pop_next()
            if not combatant.alive:
                continue
            self.time = current_time
            self.turn_number += 1
            combatant.start_turn()
            action = combatant.choose_action(context)
            combatant.perform_action(action, context)
            combatant.end_turn()
            self.timeline.schedule_next(combatant, current_time=current_time)
            self.manager.broadcast(constants.ON_ENEMY_ACTION if combatant.team is self.team_b else constants.ON_ALLY_ACTION, source=combatant)
            self.battlefield.tick()
        self.manager.broadcast("battle_end", data={"turns": self.turn_number})

    @property
    def is_finished(self) -> bool:
        return self.team_a.is_defeated or self.team_b.is_defeated

    def summary(self) -> dict:
        return {
            "turns": self.turn_number,
            "team_a_alive": [c.name for c in self.team_a.alive_members()],
            "team_b_alive": [c.name for c in self.team_b.alive_members()],
            "log": list(self.log_messages),
            "battlefield": self.battlefield.snapshot(),
        }
