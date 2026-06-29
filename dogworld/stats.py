"""Stats — the in-world consequence currency. WISDOM is the flagship.

WISDOM = the calibration stat: the measured gap between belief (Mode A) and the certified
world (Mode B). Acting on an uncertified belief costs WISDOM. The gate writes here; the
penalty string is returned to the agent's context. Stats are extensible (HEALTH, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Stats:
    values: dict[str, int] = field(default_factory=lambda: {"WISDOM": 10})
    history: list[tuple[str, int, str]] = field(default_factory=list)  # (stat, delta, reason)

    def get(self, stat: str) -> int:
        return self.values.get(stat, 0)

    def delta(self, stat: str, d: int, reason: str = "") -> str:
        """Apply a delta; return the canonical badge string, e.g. 'WISDOM -1'."""
        self.values[stat] = self.values.get(stat, 0) + d
        self.history.append((stat, d, reason))
        sign = f"+{d}" if d >= 0 else str(d)
        return f"{stat} {sign}"

    def count_losses(self, stat: str = "WISDOM") -> int:
        return sum(1 for s, d, _ in self.history if s == stat and d < 0)

    def dump(self) -> str:
        vals = "  ".join(f"{k}={v}" for k, v in self.values.items())
        return f"STATS {vals}  (events: {len(self.history)})"
