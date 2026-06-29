"""live_macro — the LIVE arbiter invokes a LEARNED CIRCUIT as one macro-action (vs re-deriving).

The dog already knows a circuit ('Confirm-then-bark'). Each turn the live MiniMax dog is shown its
goal + the circuits it can invoke (with their preconditions/products) and decides: invoke a known
circuit in one move, or take an atomic action. When it invokes a circuit, the engine retrieves it
and conducts the whole gated route at once — the agent reuses what it learned instead of
re-discovering it. Sound throughout: the macro fires only if its input terminal is warranted.

Run:  MINIMAX_API_KEY=... python3 examples/live_macro.py   (needs anthropic SDK + dogworld[circuits])
"""
import sys, pathlib, json, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, llm
from dogworld.sop import FlowStep, extrude
from dogworld.macro import CircuitLibrary, HAVE_UCO

PERSONA = (
    "You are a watchdog with LEARNED CIRCUITS — whole routines you can invoke in a single move "
    "instead of figuring out each step. Prefer invoking a known circuit when it achieves your goal "
    "and its precondition holds. Otherwise take a small atomic action."
)


def decide(goal, lib, world):
    cards = []
    for s in lib.sops:
        from dogworld.circuit import lift
        c = lift(s)
        holds = all(world.warrants(t) for t in c.inputs)
        cards.append(f"  - {s.name}: does [{' → '.join(st.action for st in s.steps)}]; "
                     f"needs {sorted(c.inputs)} ({'AVAILABLE now' if holds else 'precondition NOT met'}); "
                     f"produces {sorted(c.outputs)}")
    user = (
        f"Your goal: {goal}\n\nLearned circuits you can invoke (one move each):\n" + "\n".join(cards) +
        "\n\nReply with ONE JSON object and nothing else (start with '{'):\n"
        '  {"why":"<short>","use_circuit":"<circuit name>"}   or   {"why":"<short>","do":"sniff"}'
    )
    raw = llm.complete(PERSONA, user, max_tokens=1200)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        return json.loads(m.group(0)) if m else {"do": "sniff", "why": "(no json)"}
    except Exception:
        return {"do": "sniff", "why": "(parse error)"}


def main():
    if not llm.available() or not HAVE_UCO:
        print("Needs MINIMAX_API_KEY + anthropic + dogworld[circuits].")
        return

    world = World(); world.close("owl_present(forest)")     # the owl is in the forest (precondition holds)
    lib = CircuitLibrary([extrude("Confirm-then-bark", "Canine", [
        FlowStep("dog", "move to forest", place="forest", passed=True),
        FlowStep("dog", "see (borrowed from owl)", warrant="owl_present(forest)",
                 produces="confirmed_owl(forest)", place="forest", passed=True),
        FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)",
                 place="forest", passed=True),
    ], subdomain="Alerting", tags=("owl", "alert"), fitness=3)])

    goal = "announce any owl that is around (achieve near(dog,owl))"
    print("== live: the dog chooses to invoke a LEARNED CIRCUIT as one macro-action ==\n")
    for t in range(1, 4):
        if world.warrants("near(dog,owl)"):
            print(f"[t{t}] goal already achieved (near(dog,owl)) — done."); break
        d = decide(goal, lib, world)
        why = d.get("why", "")
        if "use_circuit" in d:
            circuit, res = lib.run_macro(d["use_circuit"], world)
            if circuit:
                print(f"[t{t}] INVOKE CIRCUIT '{circuit.name}' → {res.status}  (one move = {res.context.get('conducted')})")
            else:
                print(f"[t{t}] tried to invoke '{d['use_circuit']}' but its precondition wasn't met")
        else:
            print(f"[t{t}] atomic: {d.get('do')}")
        print(f"        ↳ {why}")

    print(f"\nfinal: near(dog,owl) achieved = {world.warrants('near(dog,owl)')}")


if __name__ == "__main__":
    main()
