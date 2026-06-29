"""curate_demo — the circuit library curates itself: reinforce, promote, decay, prune.

Each successful macro REINFORCES a route (run_count++). The promotion score = fitness (catalysis)
+ reuse, so the most catalytic AND most-used circuits rise to the top of the RAG. Aging (decay)
fades unreinforced routes; prune drops the dead. The tower keeps its useful routes and sheds the
rest — a usage-weighted bandit over proven routes.

Run: pip install dogworld[circuits]; python3 examples/curate_demo.py   (offline, no API)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, extrude
from dogworld.macro import CircuitLibrary, HAVE_UCO

ALERT = lambda: extrude("Confirm-then-bark", "Canine", [
    FlowStep("dog", "see", warrant="owl_present(forest)", produces="confirmed_owl(forest)", passed=True),
    FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)", passed=True),
], subdomain="Alerting", tags=("owl", "alert"), fitness=3)
FETCH = lambda: extrude("Fetch-the-ball", "Canine", [
    FlowStep("dog", "grab", warrant="ball_in_sight", produces="has_ball", passed=True)], tags=("ball", "fetch"), fitness=1)
TRICK = lambda: extrude("Rare-trick", "Canine", [
    FlowStep("dog", "spin", warrant="audience", produces="applause", passed=True)], tags=("trick",), fitness=0)


def show(lib, label):
    print(f"  {label}: " + " | ".join(f"{s.name}(fit={s.fitness},runs={s.run_count},score={lib.score(s):.0f})"
                                      for s in lib.top(5)))


def main():
    if not HAVE_UCO:
        print("Needs dogworld[circuits] (UCO)."); return
    lib = CircuitLibrary([ALERT(), FETCH(), TRICK()])
    print("== a fresh library ==")
    show(lib, "top")

    print("\n== the dog keeps using FETCH (it gets reinforced on each successful conduct) ==")
    for _ in range(5):
        w = World(); w.close("ball_in_sight")
        lib.run_macro("fetch the ball", w)
    show(lib, "top")
    print("   -> heavy REUSE promoted a low-fitness route above the high-fitness one.")

    print("\n== time passes: decay ages unreinforced reuse ==")
    lib.decay(); lib.decay()
    show(lib, "top")

    print("\n== prune the dead (score below floor) ==")
    dropped = lib.prune(min_score=0.5)
    print(f"   pruned: {[s.name for s in dropped]}")
    show(lib, "kept")
    print("   -> the zero-fitness, never-conducted 'Rare-trick' is gone; useful routes stay.")


if __name__ == "__main__":
    main()
