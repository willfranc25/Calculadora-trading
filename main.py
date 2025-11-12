"""Demonstration script for the arena battle engine.

Run ``python main.py`` to simulate a fight between two preconfigured
teams. The script showcases the autonomous AI, stat window overlays and
battle log.
"""
from __future__ import annotations

from arena.battle import Battle
from arena.combatant import Combatant, Team
from arena.resources import Resource
from arena.skills import BuffSkill, HealingSkill, SingleTargetAttack
from arena.stats import Stats
from arena import ui


def create_knight(name: str) -> Combatant:
    stats = Stats(
        hp=1200,
        atk=180,
        mag=80,
        defense=120,
        resistance=90,
        crit_chance=0.1,
        crit_damage=1.8,
        speed=105,
        accuracy=1.0,
        evasion=0.05,
        resistances={"physical": 0.15, "fire": -0.05},
    )
    fury = Resource(name="fury", maximum=100, value=30, gain_on_events={"on_receive_damage": 10})
    skills = [
        SingleTargetAttack(name="Golpe Escudo", power=1.0, cooldown=0, tags=["physical"]),
        BuffSkill(name="Buff Defensa", stat="defense", amount=40, duration=3, cooldown=4),
    ]
    return Combatant(name, stats, skills, tags=["light", "paladin"], resources={"fury": fury})


def create_mage(name: str) -> Combatant:
    stats = Stats(
        hp=900,
        atk=90,
        mag=220,
        defense=70,
        resistance=120,
        crit_chance=0.15,
        crit_damage=2.0,
        speed=110,
        accuracy=1.05,
        evasion=0.1,
        resistances={"magical": 0.1, "fire": 0.2, "ice": -0.1},
    )
    mana = Resource(name="mana", maximum=200, value=200, regen_per_turn=20)
    skills = [
        SingleTargetAttack(name="Rayo Arcano", power=1.4, damage_type="arcane", cooldown=1, tags=["arcane"]),
        HealingSkill(name="Heal Mage", amount=150, cooldown=2, costs={"mana": 40}),
    ]
    return Combatant(name, stats, skills, tags=["arcane", "human"], resources={"mana": mana})


def main() -> None:
    knight_a = create_knight("Sir Galahad")
    mage_a = create_mage("Iris")
    knight_b = create_knight("Black Lancer")
    mage_b = create_mage("Selene")

    team_a = Team("Orden de la Luz", [knight_a, mage_a])
    team_b = Team("Cónclave", [knight_b, mage_b])

    battle = Battle(team_a, team_b)
    battle.run(max_turns=20)

    print("=== Registro de combate ===")
    print(ui.format_log(battle.log_messages))
    print("\n=== Estado final ===")
    for combatant in team_a.members + team_b.members:
        print(ui.format_stats_window(combatant))
        print()


if __name__ == "__main__":
    main()
