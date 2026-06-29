"""sop — learning: crystallize a WARRANTED route into a replayable SOP (gated SOP-extrusion).

The SOP-extrusion pattern: bracket an event flow (start/end), and the start-event's KV becomes the
`input_signature` while the recorded events become the `steps`. Dogworld keeps that schema but adds
the soundness the gate provides:

  - **gated extrusion** — a step enters the SOP ONLY IF the gate WARRANTED it. The plain pattern
    records what agents DID; dogworld records what the WORLD VALIDATED. A learned SOP is a
    *warranted route*.
  - **fitness-ranked** — routes carry their catalytic `fitness`, not just `run_count` (the most
    catalytic routes are the best SOPs).
  - **sound replay** — `replay()` re-checks each step's warrant against the (possibly changed) world;
    a stale SOP is rejected at the first warrant that no longer holds. You can't replay a lie.

Standard SOP JSON schema (domain/subdomain, input_signature, steps, tags, run_count).
Pure stdlib — JSON dir + keyword search; no external DB.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .world import World


@dataclass
class FlowStep:
    """One recorded step of a live/sim flow, with the gate's verdict on it."""
    agent: str
    action: str
    warrant: str = ""       # the fact the world had to hold (the gate's check); "" = ungated action
    place: str = ""
    passed: bool = True      # did the gate warrant it? UNwarranted steps never enter a SOP.


@dataclass
class Step:
    order: int
    agent: str
    action: str
    warrant: str = ""
    place: str = ""


@dataclass
class SOP:
    slug: str
    name: str
    domain: str
    subdomain: str = ""
    input_signature: dict = field(default_factory=dict)   # {param: {"example":.., "required":bool}}
    steps: list[Step] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    fitness: int = 0
    run_count: int = 0
    created_at: str = ""

    def to_json(self) -> dict:
        d = asdict(self)
        return d


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def extrude(name: str, domain: str, flow: list[FlowStep], *, subdomain: str = "",
            input_signature: dict | None = None, tags: tuple[str, ...] = (),
            fitness: int = 0, created_at: str = "") -> SOP:
    """Crystallize a flow into a SOP — keeping ONLY the warranted steps (the gated extrusion)."""
    warranted = [s for s in flow if s.passed]
    steps = [Step(i + 1, s.agent, s.action, s.warrant, s.place) for i, s in enumerate(warranted)]
    return SOP(slug=_slug(name), name=name, domain=domain, subdomain=subdomain,
               input_signature=input_signature or {}, steps=steps, tags=list(tags),
               fitness=fitness, created_at=created_at)


@dataclass
class Replay:
    ok: bool
    stale_at: int | None = None     # the step order where a warrant no longer holds
    reason: str = ""


def replay(sop: SOP, world: World, *, place_of: dict[str, str] | None = None) -> Replay:
    """Re-validate the SOP against the current world: every step's warrant must still hold.

    `place_of` lets a warrant template reference `{place}` for the executing agent. A warrant that
    no longer holds = the world changed = the SOP is STALE there. This is the gate re-checking a
    learned route — you cannot replay a route whose warrants the world no longer grants."""
    place_of = place_of or {}
    for st in sop.steps:
        if not st.warrant:
            continue   # ungated action (e.g. a move) — nothing to revalidate
        fact = st.warrant.format(place=st.place or place_of.get(st.agent, ""))
        if not world.warrants(fact):
            return Replay(ok=False, stale_at=st.order, reason=f"warrant no longer holds: {fact}")
    return Replay(ok=True)


class SOPStore:
    """A directory of extruded SOPs (sops/{domain}/{slug}.json) with keyword search (the standard layout)."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def save(self, sop: SOP) -> Path:
        d = self.root / sop.domain / (sop.subdomain or "")
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{sop.slug}.json"
        p.write_text(json.dumps(sop.to_json(), indent=2))
        return p

    def load_all(self) -> list[SOP]:
        out: list[SOP] = []
        for f in sorted(self.root.rglob("*.json")):
            raw = json.loads(f.read_text())
            raw["steps"] = [Step(**s) for s in raw.get("steps", [])]
            out.append(SOP(**raw))
        return out

    def search(self, query: str) -> list[SOP]:
        """BM25-lite: rank SOPs by keyword hits across name/domain/tags/step actions, then fitness."""
        terms = [t for t in re.split(r"\W+", query.lower()) if t]
        scored = []
        for sop in self.load_all():
            hay = " ".join([sop.name, sop.domain, sop.subdomain, " ".join(sop.tags),
                            " ".join(s.action for s in sop.steps)]).lower()
            score = sum(hay.count(t) for t in terms)
            if score:
                scored.append((score, sop.fitness, sop))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [s for _, _, s in scored]
