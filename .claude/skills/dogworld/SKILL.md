---
name: dogworld
description: Use to build agents/worlds in the Dogworld engine — belief-gated, abductive, soft-RNG agents whose beliefs become world-facts only if WARRANTED (else WISDOM-1), with catalysis/emergence as the computed "good" and signal-detection calibration. Triggers on "dogworld", "add an agent/perception/action", "warrant gate", "WISDOM penalty", "abductive world", "catalysis/RAF/fitness", "calibration/d-prime", "the owl/dog world".
---

# Dogworld — how to build in it

Engine at the repo root. Read `DESIGN.md` for the architecture, then use
this. Core is stdlib-only; default sampler is `MockArbiter` (no API). **Never** make the gate depend
on a heuristic, and never let an agent grant itself warrant/reward (rule-two).

## The one pattern: an agent is a class whose decorated methods self-reflect into tools+urges

```python
from dogworld import Agent, action, perception, RngSpec, World, Stats, Engine, MockArbiter

class Owl(Agent):
    name = "owl"
    @action(rng=RngSpec(values={"p": 0.6}), closes="owl_hooted@{t}")   # closes a FOOD fact (spontaneous)
    def hoot(self): return "HOOOO"

class Dog(Agent):
    name = "dog"
    @perception(                       # a belief: fires by soft prior, abduces its warrant BACKWARD
        requires="owl_hooted@{t}",     # the fact the world must hold for the belief to be true
        abduces="near({self},owl)",    # reified ON WARRANT (effect -> cause)
        penalty="You thought you heard an owl. In fact, there was not one when you looked.",
        urge="You think you heard an owl (felt-strength {p}). Bark only if you trust it.",
        rng=RngSpec(values={"p": 0.7}))
    def bark(self): return "WOOF!"

world = World()
Engine(world, [Owl(), Dog()], stats=Stats(), arbiter=MockArbiter(seed=7)).run(12)
```

The gate adjudicates each fired perception: **warranted + consistent** -> execute, close the abduced
fact (catalysis edge `warrant -> abduced`); **unwarranted/inconsistent** -> `WISDOM -1` + the penalty
(returned to the agent, option B). Templates use `{self}` and `{t}`.

## The four things you can build

1. **A cascade / catalysis chain** — make one agent's perception `requires` another's `abduces`
   (`master.investigate requires near(dog,owl)`). `dogworld.catalysis`: `cat(f)` (downstream structure),
   `fitness(agent)`, `max_raf(reactions, food)` (emergence = a self-sustaining set; collapses w/o food).
2. **Calibration** — `dogworld.sdt`: a `Channel(d')` emits a noisy percept; `Detector(tau)` decides;
   sweep `tau` -> interior optimum that matches `optimal_threshold(...)`. Blind percept (d'=0) can't calibrate.
3. **Contradiction** — `world.declare_functional("at", subject_arity=1)` so `at(dog,barn)` blocks
   `at(dog,field)`; the gate penalizes an abduction that contradicts a closed fact.
4. **A real LLM arbiter** — `LLMArbiter(persona=...)` (MiniMax via `dogworld.llm`, key in env) reasons
   over the urges + feedback. `seams/cave_runtime.py` runs it through cave-teams' `gate(body, phi)`.

## Invariants to preserve (or you break the thesis)
- Gate checks stay **decidable** (membership + declared conflicts). Soundness = prevention, not suppression.
- "good" is **world-conferred**: `cat`/`fitness`/calibration computed from real closures, never self-granted.
- Add a test (`tests/`) + update `DESIGN.md` in the same change. Run `python tests/run_all.py` (must pass).
