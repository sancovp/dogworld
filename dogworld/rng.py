"""RngSpec — the soft, prompt-injected prior over an agent's methods.

Soft (by design): the probability is NOT a forced coin-flip. It RENDERS into the prompt as
a natural-language urge ('Urge to hoot: 0.7'); the Arbiter (LLM/mock) reads the concatenated
urges and DECIDES what to listen to. `roll()` exists for the MockArbiter to *simulate* that
decision deterministically (seeded); the LLMArbiter would instead be handed `render_urge()`.

The prior is set as DATA (`set_rng_method` / `set_rng_values`) so behavior is calibratable:
realized frequency should track the injected probability — that gap is what WISDOM measures.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class RngSpec:
    method: str = "bernoulli"          # policy family: bernoulli | weighted | always | never
    values: dict[str, float] = field(default_factory=lambda: {"p": 0.5})

    def set_method(self, method: str) -> None:
        self.method = method

    def set_values(self, **values: float) -> None:
        self.values.update(values)

    @property
    def p(self) -> float:
        if self.method == "always":
            return 1.0
        if self.method == "never":
            return 0.0
        return float(self.values.get("p", 0.5))

    def render_urge(self, action: str) -> str:
        """The prompt injection: the prior as an overridable natural-language urge."""
        return f"Urge to {action}: {self.p:.2f}"

    def roll(self, rng: random.Random) -> bool:
        """Simulate the soft decision (MockArbiter only). Seeded for determinism."""
        return rng.random() < self.p
