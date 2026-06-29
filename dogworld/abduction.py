"""Abduction — the backward flow (effect -> cause).

When a perception fires, it does NOT read the world to decide if it should fire (that would be
forward simulation). It fires by its soft prior, then PROPOSES the fact that would warrant it
and the fact it abduces. The gate is what then accepts (reify on warrant) or rejects (penalty).

  perception `hear`  requires `owl_hooted@{t}`   abduces `near({self},owl)`

`propose` just resolves the templates against the current tick + the agent; it commits nothing.
"""
from __future__ import annotations

from dataclasses import dataclass

from .agent import Agent, MethodInfo


@dataclass(frozen=True)
class Proposal:
    perception: str
    warrant: str     # the fact the world must already hold for the belief to be true
    abduced: str     # the fact closed (reified) backward if warranted & consistent
    penalty: str     # the re-narration if unwarranted/inconsistent (option B)


def propose(agent: Agent, m: MethodInfo, *, t: int, **kwargs) -> Proposal:
    """Resolve a perception's abductive contract for tick `t` (commits nothing)."""
    assert m.kind == "perception", f"{m.name} is not a perception"
    return Proposal(
        perception=m.name,
        warrant=agent.fill(m.requires, t=t, **kwargs),
        abduced=agent.fill(m.abduces, t=t, **kwargs),
        penalty=m.penalty,
    )
