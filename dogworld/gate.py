"""Gate — the |= : warrant + consistency, then act-or-penalize (option B).

This is the keystone. For a fired perception's Proposal:
  - WARRANTED (world holds the warrant) AND CONSISTENT (abduced fact doesn't contradict closed
    facts)  -> reify the abduced fact (close it), execute the perception's method, return the
    success narration.
  - UNWARRANTED (absence) OR INCONSISTENT (contradiction) -> option B: dock WISDOM and return
    the re-narration penalty. The returned string re-enters the agent's context (conditioning).

Soundness: both checks are decidable (membership + declared functional/negation), so a PASS is
prevention-grade on this fragment — the agent cannot bark-itself-into-having-heard-an-owl.
"""
from __future__ import annotations

from dataclasses import dataclass

from .abduction import Proposal
from .agent import Agent, MethodInfo
from .stats import Stats
from .world import World


@dataclass
class Verdict:
    passed: bool
    text: str            # what the tool returns (success narration OR the WISDOM penalty)
    reason: str          # machine reason: "warranted" | "unwarranted" | "inconsistent:<...>"


def gate_perception(world: World, stats: Stats, agent: Agent, m: MethodInfo,
                    prop: Proposal, *, wisdom_cost: int = 1, **call_kwargs) -> Verdict:
    # Mode-B check 1: is the belief warranted? (did the thing actually happen / is it closed?)
    if not world.warrants(prop.warrant):
        badge = stats.delta("WISDOM", -wisdom_cost, reason=f"unwarranted({prop.warrant})")
        world.log(f"{agent.name}.{m.name} UNWARRANTED -> {badge}")
        return Verdict(False, f"{badge}: {prop.penalty}", "unwarranted")

    # Mode-B check 2: is the abduced (back-filled) fact consistent with the closed world?
    ok, why = world.consistent_with(prop.abduced)
    if not ok:
        badge = stats.delta("WISDOM", -wisdom_cost, reason=f"inconsistent({prop.abduced})")
        world.log(f"{agent.name}.{m.name} INCONSISTENT -> {badge} :: {why}")
        return Verdict(False, f"{badge}: {prop.penalty}", f"inconsistent:{why}")

    # PASS: reify the abduction on warrant, then execute the method
    world.close(prop.abduced, note=f"abduced by {agent.name}.{m.name} (warrant {prop.warrant})",
                enablers=(prop.warrant,), by=f"{agent.name}.{m.name}")  # catalysis edge: warrant -> abduced
    result = m.fn(**call_kwargs)
    world.log(f"{agent.name}.{m.name} OK (warrant {prop.warrant}) -> {prop.abduced}")
    return Verdict(True, str(result), "warranted")


def fire_action(world: World, agent: Agent, m: MethodInfo, *, t: int, **call_kwargs):
    """An action fires: execute it and close its `closes` fact (a real world fact)."""
    result = m.fn(**call_kwargs)
    if m.closes:
        fact = agent.fill(m.closes, t=t, **call_kwargs)
        world.close(fact, note=f"action {agent.name}.{m.name}", food=True,
                    by=f"{agent.name}.{m.name}")  # spontaneous (RNG-driven) = the food set
    return result
