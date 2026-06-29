"""places — the world chart: dirs ARE places; agents move between them; proximity gates warrants.

Isaac's design: a place is a directory. Its `place.md` lists the AFFORDANCES available there
(what you can attempt) and the EXITS (where you can go = Read-breadcrumbs to neighbor dirs). An
agent is AT one place; its capability = intrinsic tools (its manifest) ∪ the place's affordances.
Two agents at the same place are PROXIMATE (can perceive/share). Crucially, **a belief's warrant
can only exist where its cause is** — so navigating to the right place is part of being valid.

On heaven, an agent Read()-ing into a place dir autoloads its `.claude` loadout natively. On the
host we replicate that effect: the engine reads the place's chart and injects it into the live
LLM call (same semantics, host-runnable). Pure stdlib; no neo4j.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Place:
    name: str
    affords: list[str] = field(default_factory=list)   # what you can ATTEMPT here
    exits: list[str] = field(default_factory=list)      # neighbor places (where you can GO)
    desc: str = ""
    path: Path | None = None


def _parse_place(md: Path) -> Place:
    name, affords, exits, desc = md.parent.name, [], [], ""
    for ln in md.read_text().splitlines():
        s = ln.strip()
        low = s.lower()
        if low.startswith("affords:"):
            affords = [x.strip() for x in s.split(":", 1)[1].split(",") if x.strip()]
        elif low.startswith("exits:"):
            exits = [x.strip() for x in s.split(":", 1)[1].split(",") if x.strip()]
        elif s.startswith("# "):
            desc = s[2:].strip()
    return Place(name=name, affords=affords, exits=exits, desc=desc, path=md.parent)


class PlaceWorld:
    """The world chart loaded from a dir-tree of places (each dir has a `place.md`)."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.places: dict[str, Place] = {}
        for md in sorted(self.root.glob("*/place.md")):
            p = _parse_place(md)
            self.places[p.name] = p
        self.location: dict[str, str] = {}     # agent_name -> place_name
        self.shares: dict[str, list[str]] = {}  # agent -> skills it LENDS to co-located agents

    def register_share(self, agent: str, skills: list[str]) -> None:
        """Skills this agent makes available to anyone PROXIMATE to it (the owl lends `see`)."""
        self.shares[agent] = list(skills)

    def shared_with(self, agent: str) -> dict[str, list[str]]:
        """{co-located agent -> skills it lends here} — capability gained by being near others."""
        place = self.location.get(agent)
        return {a: self.shares[a] for a in self.occupants(place, exclude=agent)
                if self.shares.get(a)}

    def spawn(self, agent: str, at: str) -> None:
        self.location[agent] = at

    def here(self, agent: str) -> Place:
        return self.places[self.location[agent]]

    def co_located(self, a: str, b: str) -> bool:
        return self.location.get(a) is not None and self.location.get(a) == self.location.get(b)

    def occupants(self, place: str, exclude: str = "") -> list[str]:
        return [a for a, p in self.location.items() if p == place and a != exclude]

    def move(self, agent: str, dest: str) -> tuple[bool, str]:
        here = self.here(agent)
        if dest not in here.exits:
            return False, f"no exit to {dest!r} from {here.name} (exits: {here.exits})"
        self.location[agent] = dest
        return True, f"{agent} moved to {dest}"

    def chart_for(self, agent: str) -> str:
        """The place loadout injected into the agent's context (its 'where am I' view)."""
        p = self.here(agent)
        others = self.occupants(p.name, exclude=agent)
        lent = self.shared_with(agent)
        lent_str = "; ".join(f"{a} lends: {', '.join(sk)}" for a, sk in lent.items()) or "(none)"
        return (
            f"You are at: {p.name} ({p.desc}).\n"
            f"Here you can attempt: {', '.join(p.affords) or '(nothing)'}.\n"
            f"Skills lent to you by those nearby: {lent_str}.\n"
            f"Exits — you may move to: {', '.join(p.exits) or '(none)'}.\n"
            f"Others here with you: {', '.join(others) or '(no one)'}."
        )

    def capability(self, agent: str, intrinsic: list[str]) -> set[str]:
        """The full action-set available to `agent` NOW = intrinsic ∪ place affords ∪ co-located shares."""
        cap = set(intrinsic) | set(self.here(agent).affords)
        for sk in self.shared_with(agent).values():
            cap |= set(sk)
        return cap
