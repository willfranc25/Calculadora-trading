"""Stat system used by combat entities.

The :class:`Stats` class stores the base attributes while
:class:`DynamicStats` manages temporary modifications such as buffs or
transformations. The design prioritises clarity and modding support: all
attributes are explicitly listed and documented to avoid hidden
behaviours.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping


STAT_NAMES = [
    "hp",
    "atk",
    "mag",
    "defense",
    "resistance",
    "crit_chance",
    "crit_damage",
    "speed",
    "accuracy",
    "evasion",
]


DAMAGE_TYPES = [
    "physical",
    "magical",
    "fire",
    "ice",
    "electric",
    "arcane",
    "true",
]


@dataclass
class Stats:
    """Immutable container with the core stats of an entity."""

    hp: float = 0.0
    atk: float = 0.0
    mag: float = 0.0
    defense: float = 0.0
    resistance: float = 0.0
    crit_chance: float = 0.0
    crit_damage: float = 1.5
    speed: float = 100.0
    accuracy: float = 1.0
    evasion: float = 0.05
    resistances: Dict[str, float] = field(default_factory=dict)

    def copy(self) -> "Stats":
        return Stats(
            hp=self.hp,
            atk=self.atk,
            mag=self.mag,
            defense=self.defense,
            resistance=self.resistance,
            crit_chance=self.crit_chance,
            crit_damage=self.crit_damage,
            speed=self.speed,
            accuracy=self.accuracy,
            evasion=self.evasion,
            resistances=dict(self.resistances),
        )


class DynamicStats:
    """Tracks current stat values including temporary modifiers."""

    def __init__(self, base: Stats) -> None:
        self.base = base.copy()
        self.current = base.copy()
        self.bonus: Dict[str, float] = {name: 0.0 for name in STAT_NAMES}
        self.resistance_bonus: Dict[str, float] = {
            damage_type: 0.0 for damage_type in DAMAGE_TYPES
        }

    def apply_modifier(self, name: str, amount: float) -> None:
        """Apply a temporary additive modifier."""
        if name not in STAT_NAMES:
            raise ValueError(f"Unknown stat {name}")
        self.bonus[name] += amount
        self._recalculate(name)

    def set_override(self, name: str, value: float) -> None:
        """Override the current value for ``name``.

        Transformations can use this API to implement drastic changes
        without touching the base stats.
        """

        if name not in STAT_NAMES:
            raise ValueError(f"Unknown stat {name}")
        setattr(self.current, name, value)

    def apply_resistance_modifier(self, damage_type: str, amount: float) -> None:
        if damage_type not in DAMAGE_TYPES:
            DAMAGE_TYPES.append(damage_type)
        self.resistance_bonus[damage_type] = self.resistance_bonus.get(damage_type, 0.0) + amount

    def get(self, name: str) -> float:
        return getattr(self.current, name) + self.bonus.get(name, 0.0)

    def get_resistance(self, damage_type: str) -> float:
        base = self.current.resistances.get(damage_type, 0.0)
        return base + self.resistance_bonus.get(damage_type, 0.0)

    def as_dict(self) -> Dict[str, float]:
        values = {name: self.get(name) for name in STAT_NAMES}
        for damage_type in DAMAGE_TYPES:
            values[f"res_{damage_type}"] = self.get_resistance(damage_type)
        return values

    def refresh(self) -> None:
        """Recalculate all stats from base + bonus."""
        for name in STAT_NAMES:
            self._recalculate(name)

    def _recalculate(self, name: str) -> None:
        setattr(self.current, name, getattr(self.base, name) + self.bonus.get(name, 0.0))

    def update_from(self, other: Mapping[str, float]) -> None:
        """Bulk update modifiers from a mapping."""
        for key, value in other.items():
            if key in STAT_NAMES:
                self.set_override(key, value)

    def scale(self, factors: Mapping[str, float]) -> None:
        """Multiply stats by provided factors.

        Useful for transformations that scale several attributes at once.
        """
        for key, factor in factors.items():
            if key in STAT_NAMES:
                self.set_override(key, getattr(self.current, key) * factor)


def combine_resistances(*resistance_maps: Iterable[Mapping[str, float]]) -> Dict[str, float]:
    """Merge multiple resistance dictionaries using addition."""
    merged: Dict[str, float] = {}
    for mapping in resistance_maps:
        for damage_type, value in mapping.items():
            merged[damage_type] = merged.get(damage_type, 0.0) + value
    return merged
