"""repair — the 5th circuit role: fix a STALE circuit, gated by re-conduction.

A circuit goes stale when `conduct()` BLOCKS at a junction whose warrant no longer holds. The
repairer finds a PRODUCER of that missing warrant (a Step or a whole sub-Circuit whose output is the
needed fact and whose own precondition holds NOW), splices it in just before the broken junction,
and ADMITS the repair only if the patched circuit then CONDUCTS — sound repair: you can't admit a
repair that doesn't conduct. If no conductable producer exists, repair escalates to the author
(re-derive). Diagnosis runs on a `world.copy()` so it never mutates the real world.

The miner/conductor/composer/author/repairer set is now complete — dogworld is a full Generator.
Requires `dogworld[circuits]` (UCO).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .circuit import Circuit, compose, HAVE_UCO
from .sop import Step
from .world import World

if HAVE_UCO:
    from uco import LinkStatus


@dataclass
class RepairResult:
    ok: bool
    circuit: Circuit | None = None
    note: str = ""


def _broken_warrant(result) -> "str | None":
    if result.status == LinkStatus.SUCCESS:
        return None
    m = re.search(r"junction not warranted:\s*(.+)$", (result.error or "").strip())
    return m.group(1).strip() if m else None


def _produces(part, fact: str) -> bool:
    return (fact in part.outputs) if isinstance(part, Circuit) else (part.produces == fact)


def _precondition_holds(part, world: World) -> bool:
    if isinstance(part, Circuit):
        return all(world.warrants(t) for t in part.inputs)
    return (not part.warrant) or world.warrants(part.warrant)


def repair(circuit: Circuit, world: World, producers: list) -> RepairResult:
    """Repair `circuit` against `world` using `producers` (Steps/Circuits that close facts).

    Splice a conductable producer of the broken warrant before the broken junction; admit the patch
    ONLY if it then conducts on the real world. Returns the repaired Circuit on success."""
    if not HAVE_UCO:
        raise RuntimeError("repair needs dogworld[circuits] (universal-chain-ontology)")
    diag = circuit.conduct(world.copy())                 # diagnose without mutating the real world
    if diag.status == LinkStatus.SUCCESS:
        return RepairResult(True, circuit, "no repair needed — already conducts")
    W = _broken_warrant(diag)
    if W is None:
        return RepairResult(False, None, f"unrepairable: {diag.error}")
    prod = next((p for p in producers if _produces(p, W) and _precondition_holds(p, world)), None)
    if prod is None:
        return RepairResult(False, None, f"no conductable producer of {W!r} → escalate to the author")
    # splice the producer just before the broken junction
    steps = list(circuit.steps)
    idx = next((i for i, s in enumerate(steps)
                if (s.warrant.format(place=s.place) if s.warrant else "") == W), len(steps))
    parts = steps[:idx] + [prod] + steps[idx:]
    repaired = compose(f"{circuit.name} (repaired)", parts, sop=circuit.sop)
    if repaired.conduct(world).status == LinkStatus.SUCCESS:   # GATE the repair on the real world
        return RepairResult(True, repaired, f"spliced a producer of {W!r}; the patch conducts")
    return RepairResult(False, None, "the patch did not conduct — rejected")
