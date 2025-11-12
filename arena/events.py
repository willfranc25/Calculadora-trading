"""Event system for battle triggers.

This module defines the building blocks for the reactive combat
experience. The :class:`EventManager` centralises subscription and event
broadcasting, while :class:`EventContext` carries data about what
happened so that listeners can reason about it.

The goal is to keep the system modular and future-proof so that new
events, conditions or payloads can be added without touching existing
code. The event identifiers are simple strings to allow designers to
define custom events in content packs without having to recompile the
engine.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, DefaultDict, Dict, Iterable, List, Tuple

EventListener = Callable[["EventContext"], None]


@dataclass
class EventContext:
    """Data object describing the context of a broadcasted battle event.

    Attributes
    ----------
    name:
        Identifier of the event being broadcast (``on_turn_start``,
        ``on_attack``...).
    source:
        The actor responsible for the event. Can be ``None`` for global
        events like the start of the battle.
    targets:
        List of primary entities affected by the event. For example the
        list of targets of a skill.
    data:
        Additional custom payload. We prefer a dictionary because it is
        easy to extend while keeping backwards compatibility. The type is
        intentionally loose so future systems (UI, audio, networking)
        can piggyback on the same event context.
    """

    name: str
    source: Any | None = None
    targets: List[Any] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def derive(self, **overrides: Any) -> "EventContext":
        """Create a modified copy of the context.

        This helper makes it convenient for listeners to rebroadcast a
        related event with small changes while preserving immutability of
        the context passed to the callbacks.
        """

        params = {
            "name": self.name,
            "source": self.source,
            "targets": list(self.targets),
            "data": dict(self.data),
        }
        params.update(overrides)
        return EventContext(**params)


class EventManager:
    """Central dispatcher for combat events.

    The manager keeps a mapping of event names to listeners and exposes a
    declarative API to register and unregister callbacks. The
    implementation intentionally avoids assumptions on the order of
    listeners so that we can later plug custom priority queues without
    breaking the contract.
    """

    def __init__(self) -> None:
        self._listeners: DefaultDict[str, List[Tuple[int, EventListener]]] = (
            defaultdict(list)
        )

    def register(self, event_name: str, listener: EventListener, *, priority: int = 0) -> None:
        """Register ``listener`` for ``event_name`` with a priority.

        Higher priority numbers are executed first. In most cases the
        default priority (``0``) is adequate, but defensive mechanics or
        overrides might request a different ordering.
        """

        listeners = self._listeners[event_name]
        listeners.append((priority, listener))
        listeners.sort(key=lambda item: item[0], reverse=True)

    def unregister(self, event_name: str, listener: EventListener) -> None:
        """Remove ``listener`` for ``event_name`` if currently registered."""

        listeners = self._listeners[event_name]
        self._listeners[event_name] = [
            (priority, registered)
            for priority, registered in listeners
            if registered is not listener
        ]

    def broadcast(self, event_name: str, *, source: Any | None = None,
                  targets: Iterable[Any] | None = None,
                  data: Dict[str, Any] | None = None) -> EventContext:
        """Notify listeners about ``event_name``.

        Parameters
        ----------
        event_name:
            Identifier of the event to broadcast.
        source:
            Optional entity responsible for the event.
        targets:
            Optional iterable with the entities affected by the event.
        data:
            Optional dictionary with custom payload. Callers can reuse
            the returned context to avoid allocations.
        """

        context = EventContext(
            name=event_name,
            source=source,
            targets=list(targets or []),
            data=dict(data or {}),
        )
        for _, listener in list(self._listeners[event_name]):
            listener(context)
        return context

    def clear(self) -> None:
        """Remove all listeners.

        Useful when resetting the battle engine between matches to avoid
        leaking references to entities from a previous fight.
        """

        self._listeners.clear()
