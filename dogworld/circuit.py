"""circuit — lift warranted routes into composable UCO Chains with gated conduction.

A learned SOP is a recorded route. A **Circuit** is that route LIFTED into a reusable component on
**universal-chain-ontology (UCO)**: each gated step is a UCO `Link` that conducts only where its
junction is WARRANTED; a Circuit is a UCO `Chain` of them. Because a Chain IS a Link (UCO is
homoiconic), a Circuit-of-Circuits IS a Circuit — composition closes for free. And UCO's Chain
short-circuits on a non-SUCCESS link, so a Circuit **stops at the first unwarranted junction** —
sound conduction, for free: you can't conduct a lie.

Terminals are INFERRED (the graph-theoretic definition): the **input** terminals are the warrants
the circuit CONSUMES that nothing inside PRODUCES (external preconditions); the **output** terminals
are the facts it PRODUCES that nothing inside CONSUMES (its deliverables). Internal couplings (a fact
produced by one step and consumed by the next) are hidden — exactly like a real component's wiring.

Requires `universal-chain-ontology` (`pip install dogworld[circuits]`). The dogworld core stays
stdlib-only; circuits are the optional, composable layer.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

try:
    from uco import Link, Chain, LinkResult, LinkStatus
    HAVE_UCO = True
except Exception:                       # pragma: no cover
    HAVE_UCO = False
    Link = object                       # type: ignore

from .sop import SOP, Step, _slug
from .world import World


if HAVE_UCO:
    class GatedStep(Link):
        """A UCO Link whose conduction is GATED by a warrant: SUCCESS (and close its product) if
        warranted, BLOCKED if not. UCO's Chain stops at a BLOCKED link → sound conduction."""

        def __init__(self, step: Step):
            self.step = step
            self.name = f"{step.agent}.{step.action}"

        async def execute(self, context=None, **kw):
            ctx = dict(context or {})
            world: World = ctx["world"]
            warrant = self.step.warrant.format(place=self.step.place) if self.step.warrant else ""
            if warrant and not world.warrants(warrant):
                return LinkResult(status=LinkStatus.BLOCKED, context=ctx,
                                  error=f"junction not warranted: {warrant}")
            if self.step.produces:               # conducting the junction closes its product
                world.close(self.step.produces.format(place=self.step.place), by=f"circuit:{self.name}")
            ctx.setdefault("conducted", []).append(self.name)
            return LinkResult(status=LinkStatus.SUCCESS, context=ctx)

        def describe(self, depth: int = 0) -> str:
            w = f"  ⟨{self.step.warrant}⟩" if self.step.warrant else ""
            return "  " * depth + f"{self.name}{w}"


def _terminals(steps: list[Step]) -> tuple[set[str], set[str]]:
    produced = {s.produces for s in steps if s.produces}
    consumed = {s.warrant for s in steps if s.warrant}
    return consumed - produced, produced - consumed     # inputs, outputs


@dataclass
class Circuit:
    name: str
    chain: "Chain"
    inputs: set
    outputs: set
    sop: SOP | None = None
    steps: list = field(default_factory=list)   # the FLATTENED leaf steps (so composites infer terminals)

    def conduct(self, world: World):
        """Run the circuit against the world (UCO LinkResult: SUCCESS, or BLOCKED-at-junction)."""
        return asyncio.run(self.chain.execute({"world": world}))

    def conducts(self, world: World) -> bool:
        return self.conduct(world).status == LinkStatus.SUCCESS

    def describe(self) -> str:
        ins = ", ".join(sorted(self.inputs)) or "(none)"
        outs = ", ".join(sorted(self.outputs)) or "(none)"
        return f"Circuit '{self.name}'\n  IN  ⟶ {ins}\n  OUT ⟵ {outs}\n  " + self.chain.describe().replace("\n", "\n  ")


def lift(sop: SOP) -> Circuit:
    """Lift a learned SOP into a Circuit (a UCO Chain of GatedSteps) with inferred terminals."""
    if not HAVE_UCO:
        raise RuntimeError("circuits need universal-chain-ontology: pip install dogworld[circuits]")
    chain = Chain(sop.slug, [GatedStep(s) for s in sop.steps])
    inputs, outputs = _terminals(sop.steps)
    return Circuit(sop.name, chain, inputs, outputs, sop, steps=list(sop.steps))


def compose(name: str, parts: list, *, sop: SOP | None = None) -> Circuit:
    """Build a hierarchical Circuit from `parts` (each a Circuit OR a Step). Because a UCO Chain IS
    a Link, a sub-Circuit's chain embeds directly as a link in the parent — Circuit-of-Circuits.
    Terminals are inferred over the FLATTENED leaf steps; conduction composes (the shared `world`
    threads sub-products to later steps), and UCO short-circuits a BLOCKED junction at any depth."""
    if not HAVE_UCO:
        raise RuntimeError("circuits need universal-chain-ontology: pip install dogworld[circuits]")
    links, leaves = [], []
    for p in parts:
        if isinstance(p, Circuit):
            links.append(p.chain); leaves.extend(p.steps)
        elif isinstance(p, Step):
            links.append(GatedStep(p)); leaves.append(p)
        else:
            raise TypeError(f"compose parts must be Circuit or Step, got {type(p).__name__}")
    chain = Chain(_slug(name), links)
    inputs, outputs = _terminals(leaves)
    return Circuit(name, chain, inputs, outputs, sop, steps=leaves)


def _find_sub(seq: list, sub: list) -> "int | None":
    n, m = len(seq), len(sub)
    for i in range(n - m + 1):
        if seq[i:i + m] == sub:
            return i
    return None


def refactor_by_motif(sops: list[SOP], *, min_len: int = 2):
    """Lift the top recurring motif into ONE shared sub-circuit, and rebuild each SOP that contains
    it as a composite that REFERENCES the sub-circuit (instead of inlining the steps). The motifs
    become shared sub-circuits — the hierarchy forms. Returns (sub_circuit, [rebuilt Circuits])."""
    motifs = detect(sops, min_len=min_len)
    if not motifs:
        return None, [lift(s) for s in sops]
    motif = motifs[0]
    msig = [(s.agent, s.action, s.warrant) for s in motif]
    sub = compose("sub:" + "-".join(s.action for s in motif), list(motif))
    rebuilt = []
    for sop in sops:
        seq = [(s.agent, s.action, s.warrant) for s in sop.steps]
        i = _find_sub(seq, msig)
        if i is None:
            rebuilt.append(lift(sop))
        else:
            parts = list(sop.steps[:i]) + [sub] + list(sop.steps[i + len(motif):])
            rebuilt.append(compose(sop.name, parts, sop=sop))
    return sub, rebuilt


def detect(sops: list[SOP], *, min_len: int = 2) -> list[list[Step]]:
    """Detect recurring warranted sub-paths (motifs) across SOPs — candidates to lift as shared
    sub-circuits. A motif = a contiguous run (by (agent, action, warrant) signature) in ≥2 SOPs."""
    def sig(s: Step): return (s.agent, s.action, s.warrant)
    counts: dict[tuple, int] = {}
    for sop in sops:
        seq, seen = [sig(s) for s in sop.steps], set()
        for L in range(min_len, len(seq) + 1):
            for i in range(len(seq) - L + 1):
                sub = tuple(seq[i:i + L])
                if sub not in seen:
                    counts[sub] = counts.get(sub, 0) + 1
                    seen.add(sub)
    by_sig = {sig(s): s for sop in sops for s in sop.steps}
    motifs = sorted((m for m, c in counts.items() if c >= 2), key=len, reverse=True)
    return [[by_sig[g] for g in m] for m in motifs]


def give_circuit(agent, circuit: Circuit) -> None:
    """Dogfood: attach a lifted circuit to an agent as a capability it can conduct."""
    if not hasattr(agent, "circuits"):
        agent.circuits = []
    agent.circuits.append(circuit)
