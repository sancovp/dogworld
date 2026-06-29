# Rule Two — the development workflow (how to change this repo without breaking it)

Read `rule-one.md` (what this dir is) and `DESIGN.md` (the architecture) first. This rule is the
discipline for *changing* it.

## The gate is the product — keep it sound
- The gate's checks must stay **decidable**: `World.warrants` = exact membership; `World.consistent_with`
  = declared negation + functional conflicts. Never make a PASS depend on a heuristic/learned judgment —
  that would turn prevention back into suppression. Semantic judgment is a *separate, future*
  layer, never folded into the sound core.
- "good" stays **world-conferred**: `cat()`/`fitness` are computed from real closures, calibration from
  real hit/false-alarm rates. Never let an agent grant itself reward, warrant, or catalysis.

## Every change is green + documented in the SAME commit
1. `python tests/run_all.py` → **all pass** before you commit. Add a test for any new behavior.
2. Update `DESIGN.md` in the same commit as any architectural change (rule 26). Mark unbuilt things
   `ASPIRATIONAL:`. Keep the module table + STATUS current.
3. Keep grades honest (G0–G9): don't write "X is Y" where it's "X maps to Y under R". The README/DESIGN
   correspondences (SDT=G2, RAF/catalysis=G5, "good=emergence=life"=G6) are load-bearing — don't inflate.

## Constraints (from rule-one, repeated because they're easy to violate)
- **No external database.** World-DB is in-memory / local sqlite only.
- **No live API calls in tests or default example paths.** `MockArbiter` is the default; `LLMArbiter`
  and `live_*` examples require an explicit key and are never run by CI.
- **Stdlib only for the core.** Seams import companion packages *if present* (try/except), never reimplement.

## Before any commit
- Secret scan: `grep -rIn -E "(sk-|api[_-]?key *= *['\"]|bearer |password *=|ghp_|AKIA)" .` → must be empty
  (env-var *names* like `MINIMAX_API_KEY` are fine; literal key *values* are not).
- If pushing to a **public** remote: de-lore first — scrub local-absolute paths and any internal
  host/project names from code + docs (provenance can live in a private note outside the repo).
