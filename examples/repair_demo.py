"""repair_demo — the 5th role: fix a STALE circuit, gated by re-conduction.

A circuit that barks at a confirmed owl goes stale in a world where the owl was never confirmed
(it BLOCKS at the bark junction). The repairer finds a conductable PRODUCER of the missing warrant
(the borrowed `see`), splices it in before the broken junction, and admits the patch only if it then
conducts. No conductable producer → escalate to the author. Diagnosis never mutates the real world.

Run: pip install dogworld[circuits]; python3 examples/repair_demo.py   (offline, no API)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, Step, extrude
from dogworld.circuit import lift, HAVE_UCO
from dogworld.repair import repair


def main():
    if not HAVE_UCO:
        print("Needs dogworld[circuits] (UCO)."); return

    bark = lift(extrude("Bark-at-owl", "Canine", [
        FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)", passed=True)]))
    see = Step(0, "dog", "see (borrowed from owl)", warrant="owl_present(forest)",
               produces="confirmed_owl(forest)")     # a known producer of the missing warrant

    print("== stale circuit: 'Bark-at-owl' needs confirmed_owl(forest), which was never established ==")
    w = World(); w.close("owl_present(forest)")        # the owl IS present, just not confirmed yet
    print(f"   conduct as-is → {bark.conduct(w.copy()).status}  (blocked at the bark junction)")

    print("\n== repair: splice a conductable producer, admit only if it re-conducts ==")
    res = repair(bark, w, producers=[see])
    print(f"   ok={res.ok}: {res.note}")
    if res.ok:
        print("   " + res.circuit.describe().replace("\n", "\n   "))
        print(f"   near(dog,owl) now produced: {w.warrants('near(dog,owl)')}")

    print("\n== negative: no owl present at all → the producer isn't conductable → escalate ==")
    res2 = repair(bark, World(), producers=[see])
    print(f"   ok={res2.ok}: {res2.note}")


if __name__ == "__main__":
    main()
