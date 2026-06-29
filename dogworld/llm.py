"""llm — the real model transport (MiniMax via the anthropic-compatible endpoint).

This is the LLM CALL, not orchestration (cave-teams does orchestration). MiniMax is reached
through the anthropic SDK pointed at `https://api.minimax.io/anthropic` with `MINIMAX_API_KEY`
(the documented bare path; the key is read from the MINIMAX_API_KEY env var). The heaven path
(`cave_teams.examples.minimax_runtime.MiniMaxRuntime`) self-authenticates but is container-only;
on the host we use this bare path.

Used by `LLMArbiter` (dogworld/arbiter.py). Never called by tests/MockArbiter.
"""
from __future__ import annotations

import os

MINIMAX_BASE_URL = "https://api.minimax.io/anthropic"
DEFAULT_MODEL = os.environ.get("CAVE_MINIMAX_MODEL", "MiniMax-M2.7-highspeed")


def available() -> bool:
    if not os.environ.get("MINIMAX_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except Exception:
        return False


def complete(system: str, user: str, *, model: str | None = None, max_tokens: int = 512,
             temperature: float = 0.7) -> str:
    """One MiniMax completion. Returns the concatenated text blocks."""
    import anthropic
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError("MINIMAX_API_KEY not in env (export it before a live run)")
    client = anthropic.Anthropic(api_key=key, base_url=MINIMAX_BASE_URL)
    msg = client.messages.create(
        model=model or DEFAULT_MODEL, max_tokens=max_tokens, temperature=temperature,
        system=system, messages=[{"role": "user", "content": user}],
    )
    return "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
