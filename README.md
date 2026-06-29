# Dogworld

**An abductive, soft-RNG, belief-gated agent-world engine.**

An agent's *belief* becomes a *world-fact* only if the world **warrants** it. Acting on an
unwarranted belief costs **WISDOM** (a calibration stat). The world is generated **backward**
by abduction; soundness is a decidable **consistency gate**; the LLM is the **sampler/arbiter**
over soft-RNG priors that inject as prompt-level urges.

> *"WISDOM −1: You thought you heard an owl. In fact, there was not one when you looked."*

Full architecture + diagrams: **[DESIGN.md](DESIGN.md)**. Why this dir exists / where it is:
**[.claude/rules/rule-one.md](.claude/rules/rule-one.md)**.

---

## Dogworld as a research program

Dogworld is a testbed in the **SSRI** program (Sanctuary System Research Institute), whose
central question is:

> **Can a sound, external, symbolic gate make an LLM agent's beliefs and actions *valid* —
> calibrated, grounded, productive — in ways the generator cannot achieve on its own?**

**The hard core (the thesis under test).** An LLM is a pure conditional sampler: it can emit a
token, a belief, or an action that *looks* right without the property actually holding ("P
without P-ness" = slop). Scaling and self-critique can only *suppress* this — a sampler checking
itself is just more sampling, so the error rate has a floor it cannot cross. **Prevention**
requires a verifier that is *not* a sampler: a sound, decidable, symbolic **gate** (an *automated
Challenger*). And the gate's verdicts — both the penalty and the reward — must be
**world-conferred, never self-granted**, or they are gameable. Dogworld is the smallest world in
which this thesis is *measured* rather than asserted.

**The model (the protective belt — the specific commitments).**
- The world is generated **backward by abduction** (a fired perception writes the fact that would
  justify it), so it is cheap and demand-driven — and kept coherent by the gate.
- The gate = **warrant** (membership) + **consistency** (negation / functional). Both decidable,
  hence *sound*: a PASS is prevention-grade on that fragment, not statistical suppression.
- **"Bad" = decoherence**: an unwarranted belief is refused and costs **WISDOM** (returned into
  the agent's context — in-context conditioning toward calibration).
- **"Good" = catalysis**: a warranted act that *enables further warranted acts*; **emergence** =
  a self-sustaining set (RAF). Both computed from real closures — world-conferred.
- **Calibration needs information**: a blind agent cannot be calibrated; an *informative percept*
  (signal detection) yields an interior optimal policy.

**What it measures (the benches, not claims).**
- `WISDOM` — the Mode-A-belief vs Mode-B-certified gap, as a number.
- Calibration — realized vs injected frequency; an **interior optimal threshold that matches
  signal-detection theory**, with the channel's `d′` recovered from hit/false-alarm rates.
- Catalysis — `cat(f)`, `fitness(agent)`, and **RAF emergence that collapses when starved of food**.

**Findings so far (graded; see DESIGN.md).** The gate *prevents* (not just suppresses) the failure
mode on its decidable fragment; calibration has an interior optimum matching SDT (**G2**); "good"
is computable as autocatalytic-set contribution (**G5**); a blind percept is provably
uncalibratable. The grander reading ("good = emergence = life = negentropy") is flagged **G6**
(resonance, not a derivation) and is *not* load-bearing.

**Open problems (the positive heuristic — what the program builds next).** population selection
(`evolve`/`season`) on fitness/catalysis; an LLM as the decision policy inside the calibration
loop; deriving an agent's *verbs* from the logic (OWL ObjectProperties → methods); and the
**semantic half of the gate** (judging whether "hunt" *means* hunting) — the standing frontier.

**Why it's part of SSRI.** Dogworld is the *world* instantiation of the program's general claim —
**a Provider (LLM) + a sound automated Challenger (gate) yields validity the Provider alone
cannot** — skinned as a world where validity is XP and emergence is the reward. The program
develops the gate's deeper machinery elsewhere; this repository ships the **runnable, measurable
core**, so the thesis can be checked, not taken on faith.

## The idea in one diagram (the causation swap)

```
IRL (forward):     proximity (cause)  ──determines──▶  hearing (effect)
DOGWORLD (reversed): hear-roll FIRES (effect) ──abduces──▶ proximity (cause)   [reified ON WARRANT]
```

You never specify the world — you specify *interaction probabilities*; a fired perception
**writes the minimal fact that justifies it**, and the gate rejects (penalizes) any abduction
that isn't warranted or contradicts the closed world. **WISDOM = the Mode-A-belief vs
Mode-B-certified gap, as a number.**

## Run it (stdlib only — no API calls, no external database)

```bash
cd dogworld
python3 tests/run_all.py            # 32 tests, no deps   (or: pytest tests/)
python3 examples/owl_dog.py         # the owl/dog cascade — bark returns the WISDOM penalty
python3 examples/calibration_bench.py  # P(hoot) -> realized freq + belief calibration
python3 examples/catalysis_demo.py  # "good" computed — the alert chain forms a RAF (emergence)
python3 examples/sdt_evolve.py      # calibration: interior optimal threshold matches SDT theory
```

Example output (cascade): WISDOM 10→7, bark calibration 0.70 (warranted 7 / fired 10).
Bench: realized hoot-freq tracks injected P(hoot); bark calibration tracks P(hoot); WISDOM
loss falls as the world gets owl-richer.

## Layout

```
dogworld/
  world.py      constraint store: close / warrants / consistent_with (negation + functional)
  stats.py      WISDOM + extensible stats
  rng.py        RngSpec — the soft prior; render_urge / roll
  agent.py      Agent: reflects its own @action/@perception methods into a manifest
  abduction.py  propose() — effect -> cause (the backward flow)
  gate.py       the |= : warrant + consistency -> act-or-penalize (option B, WISDOM -1)
  catalysis.py  the computed "good": cat(f), fitness(agent), max_raf (emergence/RAF)
  sdt.py        signal-detection percept channel: Channel(d'), Detector(tau), optimal_threshold
  arbiter.py    MockArbiter (default, seeded) | LLMArbiter (real MiniMax via llm.py)
  llm.py        MiniMax transport (anthropic SDK bare endpoint) — only for LLMArbiter
  engine.py     the tick loop + the calibration Report
  seams/        owl22python_adapter · cave_runtime · cave_bridge · bigdog_persona (import-if-present)
examples/  owl_dog · calibration_bench · catalysis_demo · sdt_evolve · live_owl_dog_cave
tests/     world · gate · agent · engine · catalysis · sdt · seams · llm_and_cave · run_all.py
```

## "Good" is computed: catalysis & emergence

`bad` = the world refused your belief (WISDOM −1, decoherence). `good` = a warranted act that
**catalyzes** further warranted structure. `python3 examples/catalysis_demo.py`:

```
owl_hooted@1 --enables--> near(dog,owl) --enables--> yard_checked@1
cat(owl_hooted)=2  cat(near)=1  cat(yard_checked)=0     fitness: owl 2 > dog 1 > master 0
RAF  FED (owl hoots): [dog.bark, master.investigate]  <- EMERGENCE
RAF  STARVED (no owl): []                              <- collapses
```

Two world-conferred axes: **WISDOM** (calibration — false beliefs cost) and **fitness/catalysis**
(productivity — `cat(f)`, `fitness(agent)`, `max_raf` in `catalysis.py`). Together they select for
*calibrated AND productive* — abstain-always keeps WISDOM but earns zero fitness.

## Live: a real LLM, orchestrated by cave-teams

```bash
MINIMAX_API_KEY=... python3 examples/live_owl_dog_cave.py   # needs anthropic SDK (+ optional CAVE_TEAMS_PATH)
```

A real **MiniMax** arbiter decides whether the dog barks; **cave-teams' `gate(DecisionLink,
WarrantGate)`** orchestrates it (the LLM decision is cave's `body`, the world-warrant + WISDOM
check is cave's `φ`). Verified:

```
[t1] owl HOOTS     | dog -> WOOF      | near(dog,owl) abduced & closed
[t2] owl is silent | dog -> penalty   | WISDOM -1: You thought you heard an owl. In fact, there was not one when you looked.
[t3-5] owl silent  | dog -> abstained | LEARNED from the t2 penalty fed back into context (in-context conditioning)
```

## Composes with (seams, reuse-not-reimplement)

- **cave-teams** — Dogworld runs ON it: `gate(DecisionLink, WarrantGate)`. `seams/cave_runtime.py` (live-verified).
- **MiniMax** — the live arbiter via the anthropic SDK bare endpoint. `dogworld/llm.py` + `arbiter.LLMArbiter`.
- **the Prompt Engineering System** (`~/.claude/skills/prompt-engineering`) — the CoR persona + the
  per-token gate (rulecatcher). `seams/bigdog_persona.py` (verified working).
- **owl22python** — OWL2/XML → agent state (define agents from logic). `seams/owl22python_adapter.py`

## Soundness (honest grade)

The gate is **prevention-grade on the decidable fragment**: `warrants` = exact membership,
`consistent_with` = declared negation + functional conflicts. It does NOT judge semantic
correctness (whether "hunt" *means* hunting) — that's the documented frontier. Calibration is
**measured**, never asserted.
