"""cave_runtime — Dogworld actually RUNNING on cave-teams (not a stub).

The architecture, wired:
  - the LLM's decision is cave's `body` Link  (DecisionLink: the arbiter picks which perception fires)
  - the world-warrant + WISDOM check is cave's `phi` Link  (WarrantGate: the |= as cave's evaluator)
  - composed with cave's `gate(body, phi)` — the μ operator. Same shared `context` dict cave threads.

So cave-teams is the orchestration substrate and the Dogworld gate is its gate condition. The
DecisionLink uses a REAL LLM (LLMArbiter -> MiniMax) by default. Requires cave-teams installed.
"""
from __future__ import annotations

import asyncio

from cave_teams.chain_ontology import Link, LinkResult, LinkStatus
from cave_teams import gate as cave_gate

from ..abduction import propose
from ..agent import Agent
from ..arbiter import Arbiter
from ..stats import Stats
from ..world import World


class DecisionLink(Link):
    """cave `body`: the agent's LLM picks which perception (if any) to act on -> ctx['proposal']."""
    name = "decide"

    def __init__(self, agent: Agent, arbiter: Arbiter):
        self.agent, self.arbiter = agent, arbiter

    async def execute(self, context=None, **kw):
        ctx = dict(context or {})
        t = ctx.get("t", 1)
        fired = self.arbiter.fired(self.agent, "perception")
        if fired:
            m = fired[0]
            p = propose(self.agent, m, t=t)
            ctx["proposal"] = {"method": m.name, "warrant": p.warrant,
                               "abduced": p.abduced, "penalty": p.penalty}
        else:
            ctx["proposal"] = None
        return LinkResult(status=LinkStatus.SUCCESS, context=ctx)


class WarrantGate(Link):
    """cave `phi`: adjudicate the belief against the world. Always approves (the turn is resolved
    either way — pass OR penalized); writes ctx['result'] + ctx['passed'] and feeds penalties back."""
    name = "warrant"

    def __init__(self, world: World, stats: Stats, agent: Agent, arbiter: Arbiter):
        self.world, self.stats, self.agent, self.arbiter = world, stats, agent, arbiter

    async def execute(self, context=None, **kw):
        ctx = dict(context or {})
        prop = ctx.get("proposal")
        ctx["approved"] = True
        if not prop:
            ctx["result"], ctx["passed"] = "(no perception fired)", None
            return LinkResult(status=LinkStatus.SUCCESS, context=ctx)
        m = self.agent.manifest[prop["method"]]
        if not self.world.warrants(prop["warrant"]):
            badge = self.stats.delta("WISDOM", -1, reason=f"unwarranted({prop['warrant']})")
            ctx["result"], ctx["passed"] = f"{badge}: {prop['penalty']}", False
        else:
            ok, _ = self.world.consistent_with(prop["abduced"])
            if not ok:
                badge = self.stats.delta("WISDOM", -1, reason=f"inconsistent({prop['abduced']})")
                ctx["result"], ctx["passed"] = f"{badge}: {prop['penalty']}", False
            else:
                self.world.close(prop["abduced"], note=f"abduced by {self.agent.name}.{m.name}",
                                 enablers=(prop["warrant"],), by=f"{self.agent.name}.{m.name}")
                ctx["result"], ctx["passed"] = str(m.fn()), True
        if ctx["passed"] is False and hasattr(self.arbiter, "add_feedback"):
            self.arbiter.add_feedback(self.agent.name, ctx["result"])  # penalty re-enters context
        return LinkResult(status=LinkStatus.SUCCESS, context=ctx)


def gated_turn(world: World, stats: Stats, agent: Agent, arbiter: Arbiter, *, t: int = 1) -> dict:
    """Run ONE Dogworld turn through cave's gate(body, phi). Returns the resolved context."""
    g = cave_gate(DecisionLink(agent, arbiter), WarrantGate(world, stats, agent, arbiter),
                  max_cycles=1)
    res = asyncio.run(g.execute({"t": t}))
    return res.context if hasattr(res, "context") else res
