"""macro — retrieve a learned circuit and conduct it as a single macro-action.

Instead of re-deriving a route step-by-step every run, an agent SEARCHES its library of learned
circuits (the RAG) for one that fits the goal, checks its INPUT terminals hold in the current world,
and CONDUCTS the whole gated route in one move. Two soundness checks compose:
  1. conductability — the retrieved circuit's input terminals must be warranted NOW (else it can't fire);
  2. gated conduction — the gate re-validates each junction as the circuit runs (UCO short-circuits a
     BLOCKED link). So a macro-action completes only if every junction is warranted — sound by construction.

If nothing conductable is retrieved, the agent falls back to deriving atomic actions. Keyword retrieval
by default (stdlib); promote SOPs to skill nodes for skilltree's BM25 RAG (`sop.promote_to_skill`).
Requires `dogworld[circuits]` (UCO) to lift/conduct.
"""
from __future__ import annotations

import re

from .sop import SOP
from .world import World

try:
    from .circuit import lift, Circuit, HAVE_UCO
except Exception:                       # pragma: no cover
    HAVE_UCO = False


class CircuitLibrary:
    """An agent's library of learned routes, retrievable by goal and conductable when warranted."""

    def __init__(self, sops: list[SOP] | None = None) -> None:
        self.sops: list[SOP] = list(sops or [])

    def add(self, sop: SOP) -> None:
        self.sops.append(sop)

    def retrieve(self, query: str) -> list[SOP]:
        """Rank learned routes by keyword hits across name/subdomain/tags/step-actions, then fitness."""
        terms = [t for t in re.split(r"\W+", query.lower()) if t]
        scored = []
        for s in self.sops:
            hay = " ".join([s.name, s.subdomain, " ".join(s.tags),
                            " ".join(st.action for st in s.steps)]).lower()
            score = sum(hay.count(t) for t in terms)
            if score:
                scored.append((score, s.fitness, s))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [s for _, _, s in scored]

    def conductable(self, query: str, world: World) -> "Circuit | None":
        """The top retrieved circuit whose INPUT terminals all hold in the world (so it CAN fire)."""
        if not HAVE_UCO:
            raise RuntimeError("macro-actions need dogworld[circuits] (universal-chain-ontology)")
        for sop in self.retrieve(query):
            c = lift(sop)
            if all(world.warrants(t) for t in c.inputs):
                return c
        return None

    def run_macro(self, query: str, world: World):
        """Retrieve a conductable circuit for `query` and conduct it in one move.

        Returns (circuit, LinkResult) on a fired macro, or (None, None) if nothing was conductable —
        the caller then falls back to deriving atomic actions."""
        c = self.conductable(query, world)
        if c is None:
            return None, None
        return c, c.conduct(world)
