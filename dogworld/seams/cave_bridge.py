"""Seam → cave-teams (orchestration). ASPIRATIONAL — imports cave-teams IF present; no env mutation.

The design (DESIGN.md §2 L9, §6 per-message):
  - `lift(agent)` -> a cave-teams Link whose body runs the agent's manifest through an Arbiter.
  - the warrant-check becomes `phi` in cave-teams' `gate(body, phi)` (the per-message |=).
  - WISDOM becomes the reward signal for `evolve`/`season` topologies.

This module does NOT run cave-teams or any live model. It provides `available()` and a thin
`make_phi(world)` predicate (a plain callable) that cave-teams could use as its gate condition,
plus a documented `lift` that wires an agent only if cave_teams imports. Honors the constraint:
nothing here touches an external env.
"""
from __future__ import annotations

from typing import Callable

from ..world import World


def available() -> bool:
    try:  # pragma: no cover
        import cave_teams  # type: ignore  # noqa
        return True
    except Exception:
        return False


def make_phi(world: World, warrant_of: Callable[[dict], str]) -> Callable[[dict], bool]:
    """Build a gate predicate for cave-teams: a message passes iff its claimed belief is warranted.

    `warrant_of(message)` extracts the warrant fact the message's belief depends on; the predicate
    returns whether the world warrants it. This is the per-MESSAGE |= (same gate genus as the
    per-act world check), expressed as a plain callable cave-teams' `gate(body, phi)` can consume.
    """
    def phi(message: dict) -> bool:
        return world.warrants(warrant_of(message))
    return phi


def lift(agent, arbiter=None):  # pragma: no cover - requires cave-teams installed
    """Lift a Dogworld agent into a cave-teams Link (only if cave_teams is importable)."""
    if not available():
        raise RuntimeError("cave-teams not importable; this seam is aspirational. "
                           "Core Dogworld runs without it.")
    from cave_teams.algebra import lift as cave_lift  # type: ignore
    from ..arbiter import MockArbiter
    arb = arbiter or MockArbiter()

    def run(_state):
        fired = arb.fired(agent, "perception")
        return {"agent": agent.name, "fired": [m.name for m in fired]}

    return cave_lift(run)
