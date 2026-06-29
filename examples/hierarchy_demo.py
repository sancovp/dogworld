"""hierarchy_demo — circuits compose: a Circuit nests Circuits (UCO Chain IS a Link).

Two things:
  1. compose() — hand-nest a whole circuit as a step inside a bigger one (Circuit-of-Circuits).
  2. refactor_by_motif() — a recurring sub-path (see→bark) across two routes is lifted into ONE
     shared sub-circuit; each route is rebuilt to REFERENCE it. The motif becomes a shared component;
     the hierarchy forms. Conduction composes at any depth, and UCO short-circuits a BLOCKED junction.

Run: pip install dogworld[circuits]; python3 examples/hierarchy_demo.py   (offline, no API)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, Step, extrude
from dogworld.circuit import lift, compose, refactor_by_motif


def main():
    # --- two learned routes that share the see→bark sub-path ---
    a = extrude("Confirm-then-bark", "Canine", [
        FlowStep("dog", "move to forest", place="forest", passed=True),
        FlowStep("dog", "see", warrant="owl_present(forest)", produces="confirmed_owl(forest)", passed=True),
        FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)", passed=True),
    ], tags=("owl",))
    b = extrude("Sniff-then-bark", "Canine", [
        FlowStep("dog", "sniff", passed=True),
        FlowStep("dog", "see", warrant="owl_present(forest)", produces="confirmed_owl(forest)", passed=True),
        FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)", passed=True),
    ], tags=("owl",))

    print("== refactor_by_motif: lift the shared see→bark into ONE sub-circuit, rebuild both routes ==")
    sub, rebuilt = refactor_by_motif([a, b])
    print(f"   shared sub-circuit: '{sub.name}'   IN {sorted(sub.inputs)}  OUT {sorted(sub.outputs)}")
    for c in rebuilt:
        print(f"\n   {c.describe()}")

    print("\n== conduct a rebuilt COMPOSITE (the whole hierarchy conducts, gated at every depth) ==")
    w = World(); w.close("owl_present(forest)")
    res = rebuilt[0].conduct(w)
    print(f"   {rebuilt[0].name} → {res.status}; conducted leaves = {res.context.get('conducted')}")
    print(f"   produced near(dog,owl): {w.warrants('near(dog,owl)')}")

    # --- hand-compose: nest a WHOLE circuit as a step in a bigger one ---
    print("\n== compose: nest a circuit as a step inside a bigger circuit ==")
    patrol = compose("Patrol-then-alert", [Step(1, "dog", "walk the perimeter"), lift(a)])
    print(f"   '{patrol.name}'  IN {sorted(patrol.inputs)}  OUT {sorted(patrol.outputs)}  (leaves: {len(patrol.steps)})")
    w2 = World(); w2.close("owl_present(forest)")
    print(f"   conduct → {patrol.conduct(w2).status}; near(dog,owl): {w2.warrants('near(dog,owl)')}")


if __name__ == "__main__":
    main()
