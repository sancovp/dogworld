"""Engine — the tick loop. perceive -> urge -> arbitrate -> abduce -> gate -> act/penalize.

Per tick, two phases (order matters so warrants exist before perceptions check them):
  Phase A — ACTIONS fire (by soft prior) and close their real facts (owl.hoot -> owl_hooted@t).
  Phase B — PERCEPTIONS fire (by soft prior); each is abduced and routed through the gate,
            which either reifies the abduced fact + executes, or docks WISDOM + re-narrates.

The Report carries the measurables: WISDOM trajectory, per-method fire counts, and per-
perception pass/fail — i.e. the calibration of belief to the certified world.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .abduction import propose
from .agent import Agent
from .arbiter import Arbiter, MockArbiter
from .gate import fire_action, gate_perception
from .stats import Stats
from .world import World


@dataclass
class Report:
    ticks: int = 0
    wisdom: list[int] = field(default_factory=list)
    fires: dict[str, int] = field(default_factory=dict)      # method -> times fired
    passes: dict[str, int] = field(default_factory=dict)     # perception -> warranted passes
    fails: dict[str, int] = field(default_factory=dict)      # perception -> penalized fails
    lines: list[str] = field(default_factory=list)

    def _inc(self, d: dict, k: str) -> None:
        d[k] = d.get(k, 0) + 1

    def calibration(self, perception: str) -> float:
        """warranted-pass rate among fires = how well belief tracked the certified world."""
        f = self.fires.get(perception, 0)
        return (self.passes.get(perception, 0) / f) if f else float("nan")

    def summary(self) -> str:
        out = [f"ran {self.ticks} ticks", f"WISDOM {self.wisdom[0] if self.wisdom else '-'} -> "
               f"{self.wisdom[-1] if self.wisdom else '-'}"]
        for p in self.passes.keys() | self.fails.keys():
            out.append(f"  {p}: fired {self.fires.get(p,0)}  warranted {self.passes.get(p,0)}  "
                       f"penalized {self.fails.get(p,0)}  calibration {self.calibration(p):.2f}")
        return "\n".join(out)


class Engine:
    def __init__(self, world: World, agents: list[Agent], stats: Stats | None = None,
                 arbiter: Arbiter | None = None) -> None:
        self.world = world
        self.agents = agents
        self.stats = stats or Stats()
        self.arbiter = arbiter or MockArbiter()
        self._t = 0

    def tick(self, report: Report) -> None:
        self._t += 1
        t = self._t
        self.world.log(f"-- tick {t} --")
        # Phase A: actions fire and close real facts
        for ag in self.agents:
            for m in self.arbiter.fired(ag, "action"):
                report._inc(report.fires, m.name)
                res = fire_action(self.world, ag, m, t=t)
                report.lines.append(f"[t{t}] {ag.name}.{m.name} -> {res}")
        # Phase B: perceptions fire, are abduced, and gated
        for ag in self.agents:
            for m in self.arbiter.fired(ag, "perception"):
                report._inc(report.fires, m.name)
                prop = propose(ag, m, t=t)
                v = gate_perception(self.world, self.stats, ag, m, prop)
                report._inc(report.passes if v.passed else report.fails, m.name)
                report.lines.append(f"[t{t}] {ag.name}.{m.name} -> {v.text}")
        report.wisdom.append(self.stats.get("WISDOM"))

    def run(self, n_ticks: int) -> Report:
        report = Report()
        report.wisdom.append(self.stats.get("WISDOM"))
        for _ in range(n_ticks):
            self.tick(report)
        report.ticks = n_ticks
        return report
