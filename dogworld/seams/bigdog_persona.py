"""Seam → the Prompt Engineering System (the deterministic prompt builder we made).

Reuses (does NOT reimplement) the `prompt-engineering` skill at
`~/.claude/skills/prompt-engineering/`:
  - `make_persona(spec)`  -> the Arbiter's system prompt (persona + reasoning CoR), deterministic.
  - `gate(text, exemplars)` -> the per-TOKEN |= : learns the CoR grammar from exemplars, lints a
    candidate, returns the orthogonal(steerable) / syntax_break(fatal) verdict.

This is the persona/CoR layer of DESIGN.md §2 (L10) and the finest grain of the gate-at-every-
scale (DESIGN.md §6). If the skill isn't importable, the functions raise a clear message; core
Dogworld never depends on this.
"""
from __future__ import annotations

import os
import sys

_SKILL_LIB = os.path.expanduser("~/.claude/skills/prompt-engineering/lib")
_SKILL_ROOT = os.path.expanduser("~/.claude/skills/prompt-engineering")


def _ensure_path() -> bool:
    if os.path.isdir(_SKILL_LIB):
        for p in (_SKILL_ROOT, _SKILL_LIB):
            if p not in sys.path:
                sys.path.insert(0, p)
        return True
    return False


def available() -> bool:
    return _ensure_path()


def build_arbiter_persona(name: str, role: str, foci: list[str], held: str,
                          decision: str, rules: list[str] | None = None,
                          output: str = "A tool selection.") -> str:
    """Deterministic Arbiter persona: a CoR over `foci` converging on `held` -> `decision`."""
    if not _ensure_path():
        raise RuntimeError(f"prompt-engineering skill not found at {_SKILL_ROOT}")
    from persona import make_persona  # type: ignore
    return make_persona({
        "name": name, "role": role,
        "reasoning": {"foci": foci, "held": held, "decision": decision},
        "rules": rules or [], "output": output,
    })


def lint_reasoning(text: str, exemplars: list[str]) -> dict:
    """The per-token gate: learn the CoR grammar from exemplars, lint `text`. Returns the verdict."""
    if not _ensure_path():
        raise RuntimeError(f"prompt-engineering skill not found at {_SKILL_ROOT}")
    from gate import gate  # type: ignore
    return gate(text, exemplars=exemplars)
