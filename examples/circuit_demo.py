"""circuit_demo — lift learned routes into UCO Circuits, conduct them (gated), dogfood into the owl.

A SOP is a recorded route; a Circuit is that route LIFTED onto universal-chain-ontology (UCO): a
Chain of gated Links with INFERRED terminals (in = warrants consumed-not-produced; out = facts
produced-not-consumed). It conducts only where every junction is warranted (UCO short-circuits a
BLOCKED link). Then we detect a shared motif across two routes, and dogfood a circuit into the OWL
— the agent now carries and conducts the lifted component.

Run: pip install dogworld[circuits]; python3 examples/circuit_demo.py   (offline, no API)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, extrude
from dogworld.circuit import lift, detect, give_circuit, HAVE_UCO, LinkStatus
from examples.owl_dog import Owl


def main():
    if not HAVE_UCO:
        print("Circuits need UCO: pip install universal-chain-ontology (or dogworld[circuits]).")
        return

    flow = [
        FlowStep("dog", "move to forest", place="forest", passed=True),
        FlowStep("dog", "see (borrowed from owl)", warrant="owl_present(forest)",
                 produces="confirmed_owl(forest)", place="forest", passed=True),
        FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)",
                 place="forest", passed=True),
    ]
    sop = extrude("Confirm-then-bark", "Canine", flow, subdomain="Alerting", tags=("owl", "bark"))
    circuit = lift(sop)

    print("== lifted Circuit (a UCO Chain of gated Links; terminals INFERRED) ==")
    print(circuit.describe())
    print()

    # conduct against a world where the input terminal holds
    w1 = World(); w1.close("owl_present(forest)")
    r1 = circuit.conduct(w1)
    print(f"== conduct (input terminal owl_present(forest) holds): {r1.status} ==")
    print(f"   conducted: {r1.context.get('conducted')}  | produced near(dog,owl): {w1.warrants('near(dog,owl)')}")

    # conduct against a world missing the input terminal — stops at the unwarranted junction
    w2 = World()
    r2 = circuit.conduct(w2)
    print(f"== conduct (input terminal MISSING): {r2.status} — stopped: {r2.error} ==")
    print("   -> sound conduction: the circuit can't complete past an unwarranted junction.\n")

    # detect a shared motif across two routes (the see→bark sub-circuit recurs)
    flow2 = [
        FlowStep("dog", "see (borrowed from owl)", warrant="owl_present(forest)",
                 produces="confirmed_owl(forest)", place="forest", passed=True),
        FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)",
                 place="forest", passed=True),
    ]
    sop2 = extrude("See-then-bark", "Canine", flow2, tags=("owl",))
    motifs = detect([sop, sop2])
    print("== detected recurring motif across both routes (a shared sub-circuit) ==")
    for m in motifs[:1]:
        print("   " + " ⟶ ".join(f"{s.agent}.{s.action}" for s in m))

    # DOGFOOD: give the lifted circuit to the OWL — it now carries + conducts the component
    owl = Owl()
    give_circuit(owl, circuit)
    w3 = World(); w3.close("owl_present(forest)")
    res = owl.circuits[0].conduct(w3)
    print(f"\n== dogfood → the OWL carries {len(owl.circuits)} circuit(s); it conducts one: {res.status} ==")
    print(f"   the owl ran a circuit lifted from the dog's learned route: {res.context.get('conducted')}")


if __name__ == "__main__":
    main()
