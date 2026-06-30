"""heaven_agent — dogworld agents ARE heaven agents (heaven_base), gated by dogworld.

Each dogworld gated verb (a perception/action) is exposed as a HEAVEN TOOL (`BaseHeavenTool`). When
the heaven MiniMax agent CALLS the tool, the tool runs the dogworld gate (warrant + WISDOM +
catalysis) and returns the verdict (WOOF, or "WISDOM -1: ..."). The agent is a real
`HeavenAgentConfig` (provider=ANTHROPIC, model="MiniMax-…" → the minimax path) run via
`BaseHeavenAgent.run` — Isaac's actual agent framework, NOT a bare anthropic-SDK call.

Run with a Python environment that has `heaven-framework` (import `heaven_base`) installed.
"""
from __future__ import annotations

from .abduction import propose
from .agent import Agent, MethodInfo
from .gate import fire_action, gate_perception
from .stats import Stats
from .world import World


def available() -> bool:
    try:
        import heaven_base  # noqa: F401
        return True
    except Exception:
        return False


def gated_tool(agent: Agent, m: MethodInfo, world: World, stats: Stats, clock: dict):
    """Wrap one dogworld gated verb as a BaseHeavenTool whose call runs the gate on the real world."""
    from heaven_base.baseheaventool import BaseHeavenTool, ToolArgsSchema

    def runner(**kwargs):
        t = clock.get("t", 1)
        if m.kind == "action":
            out = str(fire_action(world, agent, m, t=t))
        else:
            out = gate_perception(world, stats, agent, m, propose(agent, m, t=t)).text
        clock.setdefault("_log", []).append((m.name, out))   # record the ACTUAL gate verdict
        return out                          # WOOF... or "WISDOM -1: ..." — the gate's verdict

    from typing import Dict, Any
    Schema = type(f"{m.name}Args", (ToolArgsSchema,),
                  {"__annotations__": {"arguments": Dict[str, Dict[str, Any]]}, "arguments": {}})
    return type(f"{agent.name}_{m.name}_Tool", (BaseHeavenTool,), {
        "name": m.name,
        "description": (m.urge or f"{agent.name}'s {m.kind} '{m.name}'") + " (adjudicated by the world gate)",
        "func": staticmethod(runner),
        "args_schema": Schema,
        "is_async": False,
    })


def build_heaven_agent(agent: Agent, world: World, stats: Stats, *, system_prompt: str,
                       model: str = "MiniMax-M2.5-highspeed", clock: dict | None = None,
                       temperature: float = 0.7, max_tokens: int = 4000):
    """Build a heaven MiniMax agent whose TOOLS are `agent`'s gated verbs. Returns (agent, clock)."""
    from heaven_base.baseheavenagent import BaseHeavenAgent, HeavenAgentConfig
    from heaven_base.unified_chat import ProviderEnum, UnifiedChat

    clock = clock if clock is not None else {"t": 1}
    tools = [gated_tool(agent, m, world, stats, clock) for m in agent.manifest.values()]
    cfg = HeavenAgentConfig(
        name=agent.name, system_prompt=system_prompt,
        provider=ProviderEnum.ANTHROPIC, model=model,         # MiniMax routes through the anthropic path
        temperature=temperature, max_tokens=max_tokens, tools=tools,
    )
    return BaseHeavenAgent(cfg, UnifiedChat()), clock
