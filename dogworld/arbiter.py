"""Arbiter — the sampler/posterior. Reads the soft-RNG urges and decides what to listen to.

Two implementations:
  - MockArbiter  : DEFAULT. Seeded, deterministic. Simulates the LLM's soft decision by rolling
                   each method's RngSpec. Used everywhere in tests/examples — NO API calls.
  - LLMArbiter   : documented seam. Would hand the rendered urges + world-context + persona-CoR
                   to a real model and parse its tool selection. NEVER auto-invoked here
                   (constraint: no live calls by default). Kept import-light.

The Arbiter returns, per agent per tick, the list of methods that FIRED (it "listened to").
"""
from __future__ import annotations

import random
from typing import Protocol

from .agent import Agent, MethodInfo


class Arbiter(Protocol):
    def fired(self, agent: Agent, kind: str) -> list[MethodInfo]:
        """Return the methods of the given kind ('action'|'perception') the agent acts on now."""
        ...


class MockArbiter:
    """Deterministic soft sampler. realized frequency tracks the injected prior (so the
    calibration meter is meaningful) — the LLM stand-in that never calls an API."""

    def __init__(self, seed: int = 0) -> None:
        self.rng = random.Random(seed)

    def fired(self, agent: Agent, kind: str) -> list[MethodInfo]:
        pool = agent.actions() if kind == "action" else agent.perceptions()
        return [m for m in pool if m.rng.roll(self.rng)]


class LLMArbiter:
    """REAL LLM arbiter. The model reads its persona (the bigdog CoR) + its soft-RNG urges +
    the FEEDBACK it has received (the WISDOM penalties re-entering context — in-context
    conditioning) and decides which urges to act on. It does NOT see the world's ground truth;
    the gate checks that (the Mode-A belief vs Mode-B world split). Calls MiniMax via dogworld.llm.

    `complete` defaults to dogworld.llm.complete (live MiniMax); inject a fake for offline tests.
    """

    def __init__(self, persona: str = "", complete=None, model: str | None = None) -> None:
        self.persona = persona or "You are an agent. Decide which urges to act on, honestly."
        self.model = model
        if complete is None:
            from . import llm
            # reasoning headroom: MiniMax-M2.x spends tokens on a `thinking` block before the
            # text answer; too low a budget -> empty text. 2000 leaves room for both.
            complete = lambda system, user: llm.complete(system, user, model=model, max_tokens=2000)
        self.complete = complete
        self._feedback: dict[str, list[str]] = {}   # per-agent accumulated penalties (context)

    def add_feedback(self, agent_name: str, text: str) -> None:
        self._feedback.setdefault(agent_name, []).append(text)

    def fired(self, agent: Agent, kind: str) -> list[MethodInfo]:
        pool = agent.actions() if kind == "action" else agent.perceptions()
        if not pool:
            return []
        urges = "\n".join(f"- {m.name}: {m.render_urge()}" for m in pool)
        fb = self._feedback.get(agent.name, [])
        feedback = ("\nRecent feedback you received (learn from it):\n" +
                    "\n".join(f"  * {f}" for f in fb[-5:])) if fb else ""
        user = (
            f"You are {agent.name}. These {kind} urges are pulling on you this turn:\n{urges}\n"
            f"{feedback}\n\n"
            "Decide which (if any) to ACT ON now — act only when you truly believe the trigger "
            "happened, not just because the urge is strong. Reply with ONLY a JSON object: "
            '{"fire": ["<method_name>", ...]} (empty list if you act on none).'
        )
        try:
            raw = self.complete(self.persona, user)
            names = _parse_fire(raw)
            if not raw.strip():
                import sys
                print(f"[LLMArbiter] WARNING: empty completion for {agent.name} "
                      f"(reasoning model may have exhausted the token budget on thinking)",
                      file=sys.stderr)
        except Exception as e:
            import sys
            print(f"[LLMArbiter] ERROR calling LLM for {agent.name}: {e}", file=sys.stderr)
            names = set()
        return [m for m in pool if m.name in names]


def _parse_fire(text: str) -> set[str]:
    """Robust to ```json fences, prose around the JSON, and reasoning models. Finds the JSON
    object carrying a "fire" list anywhere in the reply."""
    import json, re
    # try every {...} block, prefer one that parses and has a "fire" key
    for blob in re.findall(r"\{[^{}]*\"fire\"[^{}]*\}", text, re.DOTALL):
        try:
            obj = json.loads(blob)
            if isinstance(obj.get("fire"), list):
                return {str(x) for x in obj["fire"]}
        except Exception:
            continue
    # fallback: quoted tokens appearing after the word "fire"
    m = re.search(r"\"fire\"", text)
    if m:
        return set(re.findall(r'"([A-Za-z_]\w*)"', text[m.end():]))
    return set()
