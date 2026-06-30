# Dogworld — DESIGN.md (canonical source of structural truth)

> **One line:** Dogworld is a multi-agent world engine where an agent's *belief* becomes a
> *world-fact* only if the world **warrants** it; acting on an unwarranted belief costs a
> calibration stat (**WISDOM**). The world is generated **backward** by abduction; soundness
> is a decidable **consistency gate**; the LLM is the **sampler/arbiter** over soft-RNG priors
> that inject as prompt-level urges.

This doc is the spec. Code is built to it (rule 26: one canonical design doc; `ASPIRATIONAL:`
marks anything not yet implemented). Provenance: crystallized from a design
dialogue (Dogworld / "P everywhere" / the owl-hoot→dog-bark causation swap / WISDOM −1).

---

## 0. The thesis (why this engine exists)

**Research-program framing (part of SSRI).** Dogworld is a testbed in the SSRI program, whose
central thesis is that **a Provider (an LLM) + a sound, automated Challenger (a symbolic gate)
produces validity/grounding/calibration the Provider cannot produce alone.** Each Dogworld
mechanism is an *operationalization* of that thesis (operationalize-or-it's-philosophy): the gate
is the automated Challenger; WISDOM/catalysis/calibration are the measurements. The program's
deeper gate machinery is developed elsewhere; this repo is the runnable, measurable core.

An LLM is a pure conditional sampler: it can emit "P" (a token, a belief, an action) without
"P-ness" (the property actually holding) — that's slop. You **cannot prevent** that from
inside the sampler; you need a **sound external gate**. Dogworld is that gate, made into a
*world*: the gate's verdict is returned as an in-world consequence (a stat change + a
re-narration) that **re-enters the agent's context** and conditions its next sample.

Two registers of the same fact, both implemented here:
- **Mode A (open-world / belief = existence):** "the dog heard an owl" because it sampled so.
- **Mode B (existence requires self-simulation / checking):** "...in fact there was not one
  when you looked." The world-DB is what "looking" consults.
- **WISDOM = the measured gap between Mode A and Mode B.** The gate skinned as XP.

---

## 0.5 The FOUNDATION — owl22python + the template system (`dogworld/template/`)

The engine is built on (and exists to exercise) a template system, vendored in `dogworld/template/`:
- **`pydantic_stack.RenderablePiece` / `MetaStack`** — stackable, renderable pydantic models.
- **`template_mixins.TemplateAttributeMixin` / `TemplateMethodMixin`** — `add_attribute` / `add_method`
  / `execute_template_sequence`: class-level templating that builds an object's attrs/methods FROM DATA.
- **`templated_class.TemplatedClass`** — a `BaseModel`+mixins class configurable from a dict.
- **`owl22python.owl22python`** — compiles OWL2/XML → a generated `RenderablePiece` class (one typed
  field per OWL DataProperty), instantiate, render back to an ontology-typed RDF result.

Agents are built ON this (`dogworld/template_agent.TemplateAgent`): an agent's **STATE is compiled
from an OWL ontology by owl22python**, its **VERBS are added by `add_method`** (generated, not
hand-decorated), and each verb carries the dogworld gate metadata — so every template-defined verb is
adjudicated by the warrant/WISDOM/catalysis machinery. *This is the point of the engine: the gate
runs on top of the template system, not beside it.* Requires the `[template]` extra (pydantic, jinja2).

## 1. The causation swap (the core mechanism)

Real life runs cause→effect. Dogworld runs the arrow **backward** (abduction = inference to
the best explanation), which is what makes the world cheap to generate:

```mermaid
flowchart LR
  subgraph IRL["IRL — forward / physical (expensive: needs full state)"]
    P1["proximity (cause)\nthe dog IS near"] -->|determines| H1["hearing (effect)\nso it hears the hoot"]
  end
  subgraph DW["DOGWORLD — reversed / abductive (cheap: lazy, demand-driven)"]
    H2["hear-roll FIRES (effect)\nthe dog heard"] -->|implies / abduces| P2["proximity (cause)\nso it MUST have been near"]
  end
  IRL -. swap the arrow .-> DW
```

Consequence: **you never specify the world.** You specify *interaction-probabilities*; a
fired perception **writes the minimal fact that would justify it** (`near(dog,owl)` is reified
on warrant). Relations self-assemble from perception events. BUT abduction can confabulate,
so every abduced fact must pass the **consistency gate** before it closes.

---

## 2. The layer / component architecture (static structure)

```mermaid
flowchart TB
  classDef logic fill:#e3f2fd,stroke:#1565c0;
  classDef policy fill:#fff8e1,stroke:#f9a825;
  classDef sample fill:#f3e5f5,stroke:#7b1fa2;
  classDef gate fill:#ffebee,stroke:#c62828;
  classDef world fill:#e8f5e9,stroke:#2e7d32;
  classDef orch fill:#ede7f6,stroke:#4527a0;

  subgraph L1["Definition layer (D) — logic"]
    SPEC["AgentSpec\n(state fields + action/perception methods + RngSpecs)"]:::logic
    OWL["owl22python adapter\n(OWL2/XML -> AgentSpec) — SEAM, optional"]:::logic
  end
  subgraph L2["Reflection layer"]
    MANIFEST["ActionManifest\nclass reflects its own methods -> tools + urges\n(no hand-registration)"]:::logic
  end
  subgraph L3["Policy layer (the prior)"]
    RNG["RngSpec(policy, values)\nset_rng_method / set_rng_values\n-> renders NL urge ('Urge to hoot: 0.7')"]:::policy
  end
  subgraph L4["Sampler layer (the posterior)"]
    ARB["Arbiter\nreads concatenated urges + world-context + persona\n-> selects a tool call\n(MockArbiter | LLMArbiter)"]:::sample
  end
  subgraph L5["Abduction layer"]
    ABD["propose_warrant(perception)\neffect -> cause\n(hear(hoot) -> near(self,owl))"]:::sample
  end
  subgraph L6["World-DB layer (constraint store, accumulating D)"]
    WORLD["World\nclosed facts + event trace\nwarrants() [absence] + consistent_with() [contradiction]\nin-memory | sqlite  (no external DB)"]:::world
  end
  subgraph L7["Gate layer (|=) + penalty"]
    GATE["gate(action, belief)\nwarrant & consistency ->\n  ok: execute + close fact\n  fail (B): re-narrate + WISDOM-1 (returned)"]:::gate
  end
  subgraph L8["Stats layer"]
    STATS["WISDOM (calibration) + extensible stats"]:::gate
  end
  subgraph L9["Orchestration (cave-teams) — SEAM, optional"]
    CAVE["lift(agent)->Link ; gate(body, phi=warrant) ; WISDOM=reward for evolve/season"]:::orch
  end
  subgraph L10["Persona (chaincompiler/bigdog) — SEAM, optional"]
    BIGDOG["the CoR structures the Arbiter's reasoning ; rulecatcher lints it (per-token |=)"]:::orch
  end

  OWL --> SPEC --> MANIFEST --> RNG --> ARB --> ABD --> GATE
  GATE -->|consult| WORLD
  GATE -->|on fail| STATS
  GATE -->|penalty re-enters context| ARB
  ARB -. structured by .- BIGDOG
  MANIFEST -. lifts into .- CAVE
  STATS -. reward .- CAVE
```

---

## 3. The interaction cascade (activity / sequence)

```mermaid
sequenceDiagram
  participant A as Arbiter (LLM/mock)
  participant Ag as Agent (Dog)
  participant G as Gate
  participant W as World-DB
  participant S as Stats(WISDOM)

  Note over A,W: TICK t — owl.hoot fired earlier, closed owl_hooted@t (a real fact)
  A->>Ag: select action given urges + world-context (persona-structured)
  Ag->>G: bark, predicated on belief heard(owl@t)
  G->>W: warrants("owl_hooted@t")? AND consistent_with(near(dog,owl))?
  alt warranted & consistent (Mode B confirms Mode A)
    W-->>G: yes
    G->>W: close(near(dog,owl))  %% abduction reified on warrant
    G-->>Ag: "WOOF! (heard the owl — so it was close enough)"
    Ag-->>A: success enters context
  else unwarranted (absence) OR inconsistent (contradiction)
    W-->>G: no
    G->>S: WISDOM -= 1
    G-->>Ag: "WISDOM -1: You thought you heard an owl. In fact, there was not one when you looked."
    Ag-->>A: penalty re-enters context  %% in-context conditioning toward calibration
  end
```

---

## 4. An agent turn (state machine)

```mermaid
stateDiagram-v2
  [*] --> Perceive
  Perceive --> Urge: world events roll against soft-RNG perceptions
  Urge --> Arbitrate: concat urges + context -> Arbiter "decides what to listen to"
  Arbitrate --> Abduce: selected perception proposes its warranting fact
  Abduce --> Gate: warrant + consistency check
  Gate --> Act: PASS -> execute, close fact
  Gate --> Penalize: FAIL -> WISDOM-1, re-narrate (option B)
  Act --> [*]
  Penalize --> [*]: penalty re-enters context next turn
```

---

## 5. The bijection (general ↔ system ↔ code) — the most important diagram (rule 23)

| General (theory) | Dogworld (system) | Code |
|---|---|---|
| Abduction (effect → cause) | a fired perception abduces its warrant | `abduction.py: propose_warrant` |
| Active inference (obs → hidden cause) | soft-RNG urge → Arbiter selects → world-fact | `arbiter.py`, `world.py` |
| Generative-model prior | `RngSpec(values)` rendered as an urge | `rng.py: RngSpec` |
| Posterior sampler | the Arbiter (mock default / LLM optional) | `arbiter.py` |
| Open-world closure | `close()`-on-warrant (reify on warrant) | `world.py: World.close` |
| Soundness / consistency `⊨` | warrant (absence) + contradiction check | `gate.py`, `world.py: consistent_with` |
| Reward / calibration | WISDOM (Mode-A−Mode-B gap) | `stats.py: Stats` |
| Self-describing agent | class reflects methods → tools+urges | `agent.py: Agent.manifest` |
| The gate at every scale | token/act/belief/policy/message/world | `gate.py` + seams |

---

## 6. The gate at every scale (the J-invariant — same `⊨`, many grains)

```mermaid
flowchart LR
  T["per-TOKEN\nrulecatcher (syntax)"] --> AC["per-ACT\nworld-DB warrant"]
  AC --> B["per-BELIEF\nabductive consistency\n(contradiction check)"]
  B --> P["per-POLICY\ncalibration\n(realized≈injected)"]
  P --> M["per-MESSAGE\ncave-teams gate"]
  M --> WD["per-WORLD\nglobal fact consistency"]
```

---

## 6b. Good — reward/fitness as CATALYSIS (the calculable "good")

The gate gives "bad" (WISDOM −1 = the world refused your belief = decoherence). "Good" is its
non-mirror dual: a **warranted act that CATALYZES further warranted structure**. Two axes, both
world-conferred (never self-granted), so "good" inherits the gate's soundness:

| axis | stat | measures | degenerate alone |
|---|---|---|---|
| **calibration** | WISDOM | belief tracks the world (false-positive cost) | abstain-always (cowardice) |
| **productivity** | fitness (catalysis) | warranted acts that enable more warranted acts | — |

Abstain-always keeps WISDOM high but earns **zero fitness** (no catalysis), so the two axes
together select for *calibrated AND productive* — the cowardice optimum is broken by fitness.

```mermaid
flowchart LR
  subgraph FOOD["food (spontaneous, RNG-driven actions)"]
    H["owl_hooted@t"]
  end
  H -->|enables| N["near(dog,owl)"]
  N -->|enables| Y["yard_checked@t"]
  H -. "cat=2 (root)" .- H
  N -. "cat=1" .- N
  Y -. "cat=0 (warranted but inert = neutral)" .- Y
```

Definitions (all in `catalysis.py`, computed from the real run — world-conferred):
- **`cat(f)`** = size of f's descendant set in the enablement DAG = the downstream warranted
  structure f made possible. Warranted-but-inert → 0 (neutral); cascade root → high (very good).
- **`fitness(agent)`** = Σ `cat(f)` over the facts the agent closed = its catalytic contribution.
- **emergence = a RAF** (Reflexively-Autocatalytic, Food-generated set; `max_raf`, Hordijk–Steel
  closure): the food-grounded self-sustaining set of reactions. It **collapses without food** (no
  owl → no emergence). When a RAF appears, "good" stops being a per-act event and becomes a
  standing organism. `evolve`/`season` would select on fitness/RAF-centrality.

Grades: two-error calibration ↔ signal-detection theory = **G2**; fitness-as-catalysis ↔
autocatalytic-set theory (Kauffman RAF / Eigen) = **G5** (faithful, promotable by building it —
done: the owl→dog→master chain forms a RAF and collapses when starved); "good = emergence = life
= negentropy" = **G6** (dissipative-structures resonance, not a derivation).

## 6c. Places & the world chart — the LIVE heaven-agent overlay (✅ BUILT)

Dirs are **places**. Agents **move** between them; **proximity gates the warrant**; capability is
location-dependent.

- A place = a directory with a `place.md` listing **affordances** (what you can attempt here) and
  **exits** (where you can go = Read-breadcrumbs to neighbor dirs). `dogworld/places.py: PlaceWorld`
  loads the dir-tree into the chart.
- **capability(agent, now) = intrinsic tools (the manifest) ∪ place affordances ∪ co-located
  agents' shared skills.** Tools = what you *are*; place skills = what the *place* offers; shares =
  what *being near another agent* lends (the owl lends `see` to whoever is in the forest).
- **Proximity gates the warrant.** A belief's warrant can only exist where its cause is. The owl
  hoots in `forest`; the dog's `bark` requires `owl_hooted_at({place})@{t}` — so barking in the
  `yard` (no owl) is **unwarranted → WISDOM−1**, while barking in the `forest` is warranted. A live
  agent must **navigate to where its belief can be true.**
- **The mechanism.** On heaven, an agent Read()-ing into a place dir autoloads its `.claude`
  loadout natively. On the host we replicate it: the engine reads the place chart and injects it
  into the live LLM call (same semantics, host-runnable, no heaven needed).
- **Regularization tie (§ above):** a raw place is a *hyperstructure* (a loose bundle of "what's
  here"); `place.md` + the chart **regularize** it into the typed affordances/exits the gate runs
  over.

```
world/                         dog (live MiniMax) reads its chart each tick → bark | sniff | move
  forest/place.md  (owl here)  bark in forest where owl hooted → WOOF + near() + catalysis
  yard/place.md    (no owl)    bark in yard → WISDOM −1 (navigate away to be valid)
```

**Verified LIVE** (`examples/live_places.py`, real MiniMax): the dog reasoned *"No owl here,
barking would cost wisdom. Forest is where owls roost,"* **moved itself to the forest**, then
barked validly — WISDOM held at 10, `near(dog,owl)` closed. The offline core is unchanged (the
place-world is the LLM-agent overlay; `MockArbiter` tests stay stdlib).

**Proximity skill-sharing — also VERIFIED LIVE** (`examples/live_skillshare.py`): the owl lends
`see` to whoever is in the forest; the dog can't bark validly without first *confirming* an owl,
and it can only confirm by **borrowing the owl's sight**. The live MiniMax dog discovered the
three-step plan on its own — *move to forest → use the owl's lent `see` to confirm → then bark*
(WISDOM held at 10, `confirmed_owl(forest)` + `near(dog,owl)` closed). The borrowed skill is
load-bearing: without proximity to the owl, the dog cannot act validly. (Note: M2.7 is a thinking
model — give the live call enough `max_tokens` to think AND emit, or the JSON never lands.)

ASPIRATIONAL: native heaven `.claude` autoload traversal; graph (not tree) place topology; agent
populations that `evolve` over navigation policies.

## 6e. Learning — warranted routes → replayable SOPs (gated extrusion)

The SOP-extrusion pattern: bracket an event flow, extrude a parameterized procedure (the start KV →
`input_signature`, the events → `steps`). Dogworld adds the soundness the gate provides:

- **gated extrusion** — a step crystallizes into a SOP **only if the gate warranted it**. The plain
  pattern records what agents *did*; dogworld records what the world *validated*. A learned SOP is a
  **warranted route**, not merely a frequent one (the dog's `move→see→bark` becomes a SOP; the yard
  bark it tried is slop and is dropped). This is "routes = memory, carved on warrant."
- **fitness-ranked** — routes carry their catalytic `fitness`; `SOPStore.search` ranks by hits then fitness.
- **sound replay** — `replay()` re-checks every step's warrant against the current world; a stale
  SOP (the world changed) is rejected at the first warrant that no longer holds. *You can't replay a lie.*

So learning closes the loop with the rest of the engine: the gate that adjudicates a single belief
also decides what can be *remembered as a procedure*, and the same gate re-validates it on reuse.
VERIFIED (`examples/sop_demo.py`, `tests/test_sop.py`): 4 recorded → 3 kept (slop dropped); replay ok
when warrants hold, stale at the exact step when the world changed.

**Auto-bracketing + the skilltree-RAG bridge — ✅ BUILT & LIVE-verified.** `FlowRecorder.observe(step,
success=…)` needs no manual `sop_start`/`sop_end`: it records steps and, on a warranted success,
auto-extrudes the buffered route and resets (the START is the previous reset; the END is the success).
`promote_to_skill(sop, dir)` writes the learned route as a `SKILL.md` node — so **skilltree's FTS5/BM25
RAG** (`search`, coordinate-scoped, glyph-faceted; lexical by design, dense/RRF a documented later
upgrade) can index and retrieve it. The full loop ran live (`examples/live_skillshare.py`): the MiniMax
watchdog confirmed-then-barked, the route **auto-learned** into the SOP `Confirm-then-bark`, and was
**promoted to a skilltree node**. So: act → warranted success → auto-extrude → promote → RAG-retrievable.
ASPIRATIONAL: `run_count`/fitness-driven promotion thresholds; replay a retrieved SOP as a macro-action.

## 6f. Circuits — warranted routes lifted into composable UCO components (✅ BUILT)

A SOP is a *recorded route*; a **Circuit** is that route **lifted into a reusable component** on
**universal-chain-ontology (UCO)** — the published Link/Chain homoiconic primitives:

- a **GatedStep is a UCO `Link`** that conducts (SUCCESS) only where its junction is warranted, else
  BLOCKED; a **Circuit is a UCO `Chain`** of them. Because a Chain *is* a Link, a **Circuit-of-Circuits
  is a Circuit** — composition closes for free. UCO's Chain short-circuits on a BLOCKED link, so a
  Circuit **stops at the first unwarranted junction** = *sound conduction, you can't conduct a lie.*
- **terminals are inferred** (graph-theoretic): `input` = warrants consumed-not-produced (external
  preconditions); `output` = facts produced-not-consumed (deliverables); internal couplings are hidden.
- **`detect`** finds recurring warranted sub-paths (motifs) across SOPs → shared sub-circuits.
- **`give_circuit` (dogfood)** attaches a lifted circuit to an agent as a capability — the agent now
  runs on circuits the engine lifted from its own (and others') behavior. *Self-hosting: the operator
  runs what the system designed.*

**Hierarchical composition** (`compose`, `refactor_by_motif`): a Circuit nests Circuits — because a
UCO Chain IS a Link, a sub-circuit's chain embeds directly as a link in the parent (Circuit-of-Circuits,
for free). Terminals are inferred over the FLATTENED leaf steps; conduction composes at any depth and
short-circuits a BLOCKED junction wherever it occurs. `refactor_by_motif` lifts a recurring sub-path
(e.g. `see→bark` shared by two routes) into ONE shared sub-circuit and rebuilds each route to REFERENCE
it — the motifs become shared components and the hierarchy forms (the self-hosting tower). VERIFIED
(`examples/hierarchy_demo.py`): two routes rebuilt to nest the SAME `sub:see-bark` chain object;
composites conduct end-to-end and produce their output terminal.

VERIFIED (`examples/circuit_demo.py`, `tests/test_circuit.py`): the dog's `Confirm-then-bark` lifts to
a Chain with `IN ⟶ owl_present(forest)`, `OUT ⟵ near(dog,owl)`; conducts SUCCESS when the input holds,
BLOCKED at the `see` junction when it doesn't; the `see→bark` motif is detected across two routes; and
the **owl carries + conducts a circuit lifted from the dog's route**. UCO is the optional `[circuits]`
extra — the core stays stdlib-only. This is the loop's apex: regularize → gate → learn → **lift to a
gated component** → dogfood back into the agents.

**Macro-actions (`macro.py`) — ✅ BUILT + LIVE.** `CircuitLibrary.run_macro(goal, world)` retrieves the
best-matching learned circuit (RAG), checks its **input terminals hold now** (conductability), and
**conducts the whole gated route as ONE move** — the agent reuses a learned route instead of
re-deriving it. Two soundness checks compose: conductability (precondition warranted) + gated
conduction (each junction re-validated, UCO short-circuits a BLOCKED link); nothing conductable →
fall back to atomic derivation. LIVE-verified (`examples/live_macro.py`): the MiniMax dog **chose to
invoke `Confirm-then-bark` as one macro-action** (`move→see→bark` in a single move), achieving
`near(dog,owl)`. So the circle closes: derive once → learn → lift → **retrieve & conduct as a macro**.

**Self-curation (`examples/curate_demo.py`).** The library curates itself: a successful macro
**reinforces** its route (`run_count++`); retrieval ranks by relevance then a **promotion score**
(`fitness`·catalysis + reuse); `decay` ages unreinforced routes; `prune` drops the dead. So the most
catalytic-and-reused circuits rise to the top of the RAG and the rarely-conductable ones fade — a
usage-weighted bandit over proven routes. VERIFIED: heavy reuse promoted a low-fitness route above a
high-fitness one; decay aged it; prune removed a zero-fitness never-conducted route. The tower keeps
what works and sheds the rest.

## 6g. The five circuit roles — dogworld as a Generator (the meta-architecture)

The circuit primitives form five roles. Four are deterministic ops; two need generation (author,
repairer) — so the meta-team is **2 LLM policies over 3 gated tools**, not five chat agents:

| role | dogworld | kind |
|---|---|---|
| **miner** | `FlowRecorder` + `detect` (auto-bracket → extrude warranted routes) | tool |
| **conductor** | `Circuit.conduct` / `macro.run_macro` | tool |
| **composer** | `compose` / `refactor_by_motif` | tool (judgment) |
| **author** | the `LLMArbiter` deriving a NEW route when none fits | LLM policy |
| **repairer** | `repair` — splice a conductable producer of a broken warrant; admit iff it re-conducts | LLM policy / tool |

**The keystone discipline:** the meta-team is itself **gated** — a mined/composed/repaired/authored
circuit may enter the library only if it **conducts (warranted)**. Soundness lifts to the meta-level;
ungated this would be confabulatory runaway, gated it is super-compilation (the operator runs on a
self-curating tower the system designed). A dogworld Circuit IS a UCO `Chain` IS a cave-teams `Link`,
so a gated **cave-team** over the shared `CircuitLibrary` is type-compatible by construction.

**The system frame (DUO/OVP triad):** dogworld = the **Generator**; the meta-team = the automated
**Challenger/researcher** running experiments over it; an **Observer** watches the researcher; a
harvesting loop turns the observed run into papers (web-search for support). The Generator (this repo)
is built; the researcher+observer get a hookup to an external simulation-research system; the
paper-writer/harvester is solved elsewhere (SSRI) — **not built here.** The Generator's job is to emit
clean, gated, observable structure (every gate verdict, WISDOM/catalysis, circuit lift/conduct/repair)
so the experiments are measurable and the paper-pieces write themselves.

## 7. Module plan (what gets built)

| module | responsibility | status |
|---|---|---|
| `dogworld/world.py` | constraint store: `close`, `warrants`, `consistent_with` (mutex/negation), event trace, optional sqlite | BUILD |
| `dogworld/stats.py` | `Stats` (WISDOM + extensible), deltas, history | BUILD |
| `dogworld/rng.py` | `RngSpec` (policy+values), NL-urge renderer, soft-roll | BUILD |
| `dogworld/agent.py` | `Agent` base: reflect methods → `manifest` (tools+urges); `set_rng_method/values` | BUILD |
| `dogworld/abduction.py` | `propose_warrant`: perception → warranting fact (effect→cause) | BUILD |
| `dogworld/gate.py` | the `⊨`: warrant+consistency → act-or-penalize(B, WISDOM−1, re-narrate); records catalysis edges | BUILD |
| `dogworld/catalysis.py` | the calculable "good": `cat(f)`, `fitness(agent)`, `max_raf` (emergence detection) | ✅ BUILT |
| `dogworld/sdt.py` | the informative-percept channel: `Channel`(d′), `Detector`(τ), `recovered_dprime`, `optimal_threshold` — makes calibration possible | ✅ BUILT |
| `dogworld/sop.py` | **learning**: `extrude` a flow → a SOP keeping ONLY warranted steps · `SOPStore` (search) · `replay` re-validates each step's warrant (stale routes rejected) | ✅ BUILT |
| `dogworld/circuit.py` | **circuits**: `lift` a SOP → a UCO `Chain` of gated `Link`s (homoiconic), terminals inferred, conducts only where warranted · `detect` motifs · `give_circuit` (dogfood) | ✅ BUILT (`[circuits]` extra = UCO) |
| `dogworld/macro.py` | **macro-actions + self-curation**: `CircuitLibrary` retrieves a circuit, conducts the whole route as ONE move (else falls back); reinforces on success, ranks by fitness+reuse, `decay`/`prune` curate the tower | ✅ BUILT + LIVE-verified |
| `dogworld/repair.py` | **circuit repairer** (the 5th role): a stale circuit (BLOCKED at a junction) is fixed by splicing a conductable PRODUCER of the missing warrant; admitted only if it re-conducts (gated repair); else escalate to the author | ✅ BUILT |
| `dogworld/places.py` | the world chart: `PlaceWorld` over a dir-tree (places, exits, move, proximity, capability, shares) | ✅ BUILT (live-verified) |
| `dogworld/arbiter.py` | `Arbiter` protocol; `MockArbiter` (deterministic/seeded); `LLMArbiter` (REAL — live MiniMax via `dogworld/llm.py`) | ✅ BUILT |
| `dogworld/llm.py` | the model transport: MiniMax via anthropic SDK + `MINIMAX_API_KEY` (bare path; host-runnable) | ✅ BUILT |
| `dogworld/seams/cave_runtime.py` | **Dogworld running ON cave-teams**: `gate(DecisionLink, WarrantGate)` — LLM decision = body, world-warrant+WISDOM = φ | ✅ BUILT + LIVE-VERIFIED |
| `examples/live_owl_dog_cave.py` | live MiniMax arbiter over cave's gate — the full loop incl. in-context conditioning | ✅ BUILT + LIVE-VERIFIED |
| `dogworld/engine.py` | the tick loop: perceive→urge→arbitrate→abduce→gate→act/penalize; calibration meter | BUILD |
| `dogworld/seams/owl22python_adapter.py` | OWL2/XML → `AgentSpec` (import owl22python if present; else minimal local parse) | ✅ BUILT |
| `dogworld/seams/cave_bridge.py` | `lift(agent)`→Link, `phi`=warrant, WISDOM=reward (import cave-teams if present) | 🟡 `make_phi` BUILT; `lift` ASPIRATIONAL (needs cave-teams installed) |
| `dogworld/seams/bigdog_persona.py` | load the bigdog CoR as Arbiter system-prompt; rulecatcher lint hook | ✅ BUILT + VERIFIED (prompt-engineering skill end-to-end) |
| `examples/owl_dog.py` | the owl/dog world wired end-to-end | ✅ BUILT |
| `examples/calibration_bench.py` | set `P(hoot)=0.7` → measure realized vs injected | ✅ BUILT |
| `tests/` | world, gate (absence+contradiction), rng, agent-reflection, engine cascade, calibration | ✅ BUILT — 17/17 pass |

### STATUS (built 2026-06-28; then LLM+cave wired live)
All core modules + examples + seams + tests BUILT and VERIFIED. `python3 tests/run_all.py` → **36 passed, 0 failed** (offline, no API, no external DB). **Live place-world (§6c) BUILT + VERIFIED LIVE** — a real MiniMax dog navigated dir-places (forest/yard) to where its bark is warranted; it reasoned about WISDOM, moved to the forest, barked validly (WISDOM held at 10). **Signal-detection calibration (`sdt.py`) BUILT** — interior optimum matches SDT theory, `d′` recovered, blind percept proven uncalibratable. **Catalysis/emergence (§6b) BUILT** (`catalysis.py` + `examples/catalysis_demo.py`): the owl→dog→master chain forms a RAF (fitness owl=2 > dog=1 > master=0, the owl is the catalytic root) and the RAF collapses when starved of food. Offline cascade/bench: WISDOM 10→7, bark calibration 0.70; realized hoot-freq tracks injected P; WISDOM-loss falls as the world gets owl-richer.

**LIVE (real LLM + cave-teams), `examples/live_owl_dog_cave.py` (set MINIMAX_API_KEY first):** a real **MiniMax** arbiter, orchestrated by **cave-teams' `gate(DecisionLink, WarrantGate)`** (the LLM decision is the `body` Link; the world-warrant + WISDOM check is the `φ` Link). Verified run:
```
[t1] owl HOOTS     | dog -> WOOF      | near(dog,owl) abduced & closed
[t2] owl is silent | dog -> penalty   | WISDOM -1: You thought you heard an owl. In fact, there was not one when you looked.
[t3-5] owl silent  | dog -> abstained | (LEARNED from the t2 penalty fed back into context — in-context conditioning)
```
The prompt-engineering seam is verified end-to-end (builds the BIGDOG CoR persona; rulecatcher gate lints, 29 rules) — used for the gate/persona, NOT as the arbiter's prose-demanding system prompt (that conflicts with the JSON tool-selection contract; the bigdog gate lints reasoning separately).

Remaining ASPIRATIONAL: OWL ObjectProperties→methods (verbs from logic), the **semantic half of the gate** (judging meaning — the program's frontier), multi-agent cave topologies beyond the single gate (evolve/season on **fitness/catalysis**), packaging `owl22python` as an importable dependency.

**The informative-percept channel — ✅ BUILT (`sdt.py` + `examples/sdt_evolve.py`).** Blind
soft-RNG firing cannot be *calibrated* (a perception that fires independently of ground truth has
no interior optimum). So the world now emits a **noisy percept** correlated with truth
(equal-variance Gaussian SDT: `signal|owl ~ N(d′,1)`, `signal|¬owl ~ N(0,1)`); the agent barks iff
the signal exceeds its threshold `τ`. Every bark is adjudicated by the REAL gate, so the reward is
`net(τ) = fitness(catalysis from hits) − WISDOM_loss(false alarms) − miss_cost·misses`. **Verified
result:** with `d′=2` there is a clean **interior optimum** (`τ*≈+0.75`) that **matches the
SDT-optimal criterion** (`+0.65`), and the channel's `d′` is **recovered** (`z(HR)−z(FAR)=2.03`).
With `d′=0` the optimum vanishes (HR≈FAR at every τ) — *a blind agent cannot be calibrated*, the
finding confirmed. This unifies the two axes: WISDOM (calibration via τ) × catalysis (productivity
via the gate) selected in one landscape. ASPIRATIONAL remainder: drive a population `evolve` over
`τ` on cave-teams `season`; let the `LLMArbiter` (which reasons over the percept) be the policy in
place of a fixed threshold.

### Design note — sampler vs. live LLM
The default sampler is `MockArbiter` (deterministic, offline) so the engine is fully testable without a model. `LLMArbiter` wires a live **MiniMax** arbiter, and `cave_runtime.py` runs Dogworld ON cave-teams' `gate` (the LLM decision is `body`, the world-warrant check is `φ`). The host live path needs only `MINIMAX_API_KEY` in env + the anthropic SDK + the bare endpoint.

## 8. Constraints (hard)
- **No external database.** World-DB = in-memory or local sqlite only.
- **No live API calls by default.** `MockArbiter` is the default sampler; `LLMArbiter` exists but is never auto-invoked in tests/examples.
- **Stdlib only** for the core (no new pip installs). Seams import companion packages *if present* (try/except), never reimplement them (reuse rule).
- **Only write inside the repo.**

## 9. Soundness note (honest grade)
The gate is **prevention-grade (sound) on the decidable fragment**: `warrants` = exact set
membership; `consistent_with` = declared mutex/negation pairs. It does NOT judge semantic
correctness (whether "hunt" means hunting) — that's the documented frontier (the semantic half of the gate). Calibration is **measured**, not asserted. Correspondences to active-inference/abduction
are **G2** (same machine); "self-simulating qua its own world" is **G6** (right shape, the apex
direction, not claimed as achieved).
