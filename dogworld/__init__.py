"""Dogworld — an abductive, soft-RNG, belief-gated agent-world engine.

An agent's belief becomes a world-fact only if the world WARRANTS it; acting on an unwarranted
belief costs WISDOM (the calibration stat). The world is generated backward by abduction;
soundness is a decidable consistency gate; the LLM is the sampler over soft-RNG priors. See
DESIGN.md for the full architecture.
"""
from .world import World, Fact
from .stats import Stats
from .rng import RngSpec
from .agent import Agent, action, perception, MethodInfo
from .abduction import propose, Proposal
from .gate import gate_perception, fire_action, Verdict
from .arbiter import Arbiter, MockArbiter, LLMArbiter
from .engine import Engine, Report
from . import catalysis

__all__ = [
    "World", "Fact", "Stats", "RngSpec", "Agent", "action", "perception", "MethodInfo",
    "propose", "Proposal", "gate_perception", "fire_action", "Verdict",
    "Arbiter", "MockArbiter", "LLMArbiter", "Engine", "Report", "catalysis",
]
__version__ = "0.1.0"
