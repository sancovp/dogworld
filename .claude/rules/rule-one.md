# Rule One — what this directory is (read me first)

## Location & identity
- **This repo** — the canonical source for the **Dogworld** engine.
- **Created:** 2026-06-28, during an autonomous build session.
- **What it is:** a multi-agent world engine where an agent's *belief* becomes a *world-fact*
  only if the world **warrants** it; acting on an unwarranted belief costs a calibration stat
  (**WISDOM**). The world is generated **backward** by abduction; soundness = a decidable
  **consistency gate**; the LLM is the **sampler/arbiter** over soft-RNG priors that inject as
  prompt-level urges. (The owl-hoot → dog-bark "causation swap"; WISDOM −1.)

## The single source of structural truth
- **`DESIGN.md`** (this dir) — the full architecture with mermaid diagrams (layer, sequence,
  state machine, the general↔system↔code bijection, the gate-at-every-scale). Read it before
  changing anything. Update it in the same change as any architectural decision (rule 26).

## Provenance (where this came from)
Part of the **SSRI** research program (a testbed for its thesis: Provider + a sound automated
Challenger > Provider alone). Crystallized from a design dialogue (the "Dogworld / P everywhere"
thread). Companion projects, used only as optional import-if-present seams (Dogworld runs
standalone without them):
- `owl22python` — OWL → Python → agent (the define+simulate substrate)
- `cave-teams` — the agent-composition / orchestration algebra
- a prompt-engineering skill — deterministic persona + per-token gate

## Hard constraints (honored by every build step here)
- **No external database.** World-DB is in-memory or local sqlite only.
- **No live LLM/API calls by default.** `MockArbiter` is the default sampler; `LLMArbiter` is
  documented but never auto-run in tests/examples.
- **Stdlib only** for the core. Seams import companion packages *if present* (try/except) and
  **never reimplement** them (the reuse rule).
- **Work stays inside this repo.**

## How to run / verify
```bash
cd dogworld
python3 -m pytest tests/ -q            # or: python3 tests/run_all.py
python3 examples/owl_dog.py            # the owl/dog cascade
python3 examples/calibration_bench.py  # P(hoot)=0.7 -> realized frequency
```

## The job here
Build out what `DESIGN.md` specifies, keep `DESIGN.md` current, keep the gate **sound**
(decidable checks only), and keep WISDOM **measured** (never asserted). The gate is the product.
