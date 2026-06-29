"""catalysis — the calculable "good": reward/fitness as catalytic contribution to emergence.

The thesis (from the design dialogue): bad = decoherence (an unwarranted act, rejected); good =
CATALYSIS (a warranted act that ENABLES further warranted closures); emergence = a RAF appears
(a Reflexively-Autocatalytic, Food-generated set — a self-sustaining loop of warranted acts);
fitness = an agent's catalytic contribution to that, integrated.

Two computations:
  REALIZED (over what actually happened — `World.enables`):
    cat(world, f)      = the downstream warranted structure f made possible (descendant count)
    fitness(world)     = per-agent sum of cat() over the facts it closed
  STRUCTURAL (over the reaction network — the agents' specs):
    max_raf(reactions, food) = the maximal RAF (Hordijk–Steel closure): which perceptions are
                               food-grounded, i.e. the self-sustaining emergent set

All world-conferred (measured from actual closures / the real network), never self-granted —
so "good" inherits the gate's soundness. No external DB; pure stdlib graph math.
"""
from __future__ import annotations

from dataclasses import dataclass

from .world import Fact, World


# ── REALIZED catalysis (over the run's enablement DAG) ───────────────────────────────
def descendants(world: World, f: str) -> set[str]:
    """All facts reachable from f via catalysis edges (everything f helped enable, transitively)."""
    seen: set[str] = set()
    stack = list(world.enables.get(f, ()))
    while stack:
        g = stack.pop()
        if g in seen:
            continue
        seen.add(g)
        stack.extend(world.enables.get(g, ()))
    return seen


def cat(world: World, f: str) -> int:
    """Catalytic value of f = how much downstream warranted structure it made possible.

    Path-credit form: the size of f's descendant set in the enablement DAG. A warranted-but-inert
    fact (nothing requires it) scores 0 (= neutral, not good). A root that triggers a long cascade
    scores high (= very good)."""
    return len(descendants(world, f))


@dataclass
class Fitness:
    by_agent: dict[str, int]
    by_fact: dict[str, int]

    def top(self) -> str:
        return max(self.by_agent, key=self.by_agent.get) if self.by_agent else "(none)"


def fitness(world: World) -> Fitness:
    """Per-agent fitness = sum of cat(f) over the facts that agent closed (its catalytic output)."""
    by_fact = {f: cat(world, f) for f in world.facts}
    by_agent: dict[str, int] = {}
    for f, agent_method in world.closed_by.items():
        agent = agent_method.split(".")[0]
        by_agent[agent] = by_agent.get(agent, 0) + by_fact.get(f, 0)
    return Fitness(by_agent=by_agent, by_fact=by_fact)


# ── STRUCTURAL RAF (over the reaction network = the agents' specs) ────────────────────
@dataclass(frozen=True)
class Reaction:
    """A perception as a reaction: catalysed by `requires` (predicate), produces `produces`."""
    name: str
    requires: str   # predicate (args stripped)
    produces: str   # predicate


def _pred(template: str) -> str:
    """Predicate name of a fact/template (strip args + tick suffix + {placeholders})."""
    base = template.split("(")[0].split("@")[0].strip()
    return base


def reactions_from_agents(agents) -> list[Reaction]:
    """Read each agent's perception manifest into the reaction network (predicate level)."""
    rs: list[Reaction] = []
    for ag in agents:
        for m in ag.perceptions():
            rs.append(Reaction(f"{ag.name}.{m.name}", _pred(m.requires), _pred(m.abduces)))
    return rs


def max_raf(reactions: list[Reaction], food: set[str]) -> list[Reaction]:
    """Maximal Reflexively-Autocatalytic Food-generated set (Hordijk–Steel closure).

    A reaction is supported when its catalyst (`requires`) is available (food or produced by an
    already-supported reaction). Iterate the food-grounded closure to a fixpoint; the supported
    reactions ARE the RAF = the self-sustaining emergent structure. Returns [] if nothing is
    food-grounded (no emergence)."""
    food_preds = {_pred(f) for f in food}
    available = set(food_preds)
    raf: list[Reaction] = []
    changed = True
    while changed:
        changed = False
        for r in reactions:
            if r in raf:
                continue
            if r.requires in available:        # catalyst present -> reaction fires
                raf.append(r)
                if r.produces not in available:
                    available.add(r.produces)
                changed = True
    return raf
