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
    """A SELF-CURATING library of learned routes. Retrieval ranks by relevance then a PROMOTION
    score (`fitness` × catalysis + `run_count` reuse); a successful macro REINFORCES (run_count++);
    `decay` ages unreinforced routes; `prune` drops the dead. So the most catalytic, most-reused
    circuits rise to the top of the RAG and the rarely-conductable ones fade — the tower curates
    itself (a usage-weighted bandit over proven routes)."""

    def __init__(self, sops: list[SOP] | None = None, *, w_fitness: float = 1.0) -> None:
        self.sops: list[SOP] = list(sops or [])
        self.w_fitness = w_fitness

    def add(self, sop: SOP) -> None:
        self.sops.append(sop)

    def score(self, sop: SOP) -> float:
        """Promotion score: catalytic value + proven reuse."""
        return self.w_fitness * sop.fitness + sop.run_count

    def retrieve(self, query: str) -> list[SOP]:
        """Rank by keyword relevance, then by PROMOTION score (so promoted routes surface first)."""
        terms = [t for t in re.split(r"\W+", query.lower()) if t]
        scored = []
        for s in self.sops:
            hay = " ".join([s.name, s.subdomain, " ".join(s.tags),
                            " ".join(st.action for st in s.steps)]).lower()
            rel = sum(hay.count(t) for t in terms)
            if rel:
                scored.append((rel, self.score(s), s))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [s for _, _, s in scored]

    # ---- self-curation -------------------------------------------------------
    def decay(self, gamma: float = 0.8) -> None:
        """Age every route's reuse: run_count *= gamma. Reinforced routes hold; unused ones fade."""
        for s in self.sops:
            s.run_count = int(s.run_count * gamma)

    def prune(self, min_score: float = 0.5) -> list[SOP]:
        """Drop routes whose promotion score has decayed below `min_score`. Returns the pruned ones."""
        keep, dropped = [], []
        for s in self.sops:
            (keep if self.score(s) >= min_score else dropped).append(s)
        self.sops = keep
        return dropped

    def top(self, k: int = 3) -> list[SOP]:
        """The currently-promoted routes (highest promotion score)."""
        return sorted(self.sops, key=self.score, reverse=True)[:k]

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
        res = c.conduct(world)
        from .circuit import LinkStatus
        if res.status == LinkStatus.SUCCESS and c.sop is not None:
            c.sop.run_count += 1            # REINFORCE: a route that conducts gets promoted
        return c, res
