"""Text-mode helpers representing the combat UI."""
from __future__ import annotations

from typing import Iterable

from .combatant import Combatant


def format_stats_window(combatant: Combatant) -> str:
    """Return a formatted string representing the stats window."""

    snapshot = combatant.snapshot()
    lines = [f"=== {snapshot['name']} ===", f"HP: {snapshot['hp']:.0f}/{snapshot['max_hp']:.0f}"]
    lines.append("-- Stats --")
    for name, value in snapshot["stats"].items():
        lines.append(f"{name}: {value:.2f}")
    lines.append("-- Effects --")
    if snapshot["effects"]:
        for effect, data in snapshot["effects"].items():
            lines.append(f"{effect} (dur {data['duration']} st {data['stacks']})")
    else:
        lines.append("None")
    lines.append("-- Resources --")
    for name, value in snapshot["resources"].items():
        lines.append(f"{name}: {value:.1f}")
    lines.append("-- Cooldowns --")
    for name, value in snapshot["cooldowns"].items():
        lines.append(f"{name}: {value}")
    return "\n".join(lines)


def format_log(log: Iterable[str]) -> str:
    return "\n".join(log)
