import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, Step, extrude
from dogworld.circuit import lift, HAVE_UCO
from dogworld.repair import repair


def _bark():
    return lift(extrude("Bark-at-owl", "Canine", [
        FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)", passed=True)]))


_SEE = Step(0, "dog", "see", warrant="owl_present(forest)", produces="confirmed_owl(forest)")


def test_repair_splices_producer_and_admits():
    if not HAVE_UCO:
        return
    w = World(); w.close("owl_present(forest)")        # owl present, not yet confirmed -> bark blocks
    res = repair(_bark(), w, producers=[_SEE])
    assert res.ok and res.circuit is not None
    assert [s.action for s in res.circuit.steps] == ["see", "bark"]   # producer spliced before bark
    assert w.warrants("near(dog,owl)")                                 # the patch conducted on the real world


def test_repair_noop_when_already_conducts():
    if not HAVE_UCO:
        return
    w = World(); w.close("confirmed_owl(forest)")      # bark's warrant already holds
    res = repair(_bark(), w, producers=[_SEE])
    assert res.ok and "no repair needed" in res.note


def test_repair_escalates_when_no_conductable_producer():
    if not HAVE_UCO:
        return
    res = repair(_bark(), World(), producers=[_SEE])   # producer needs owl_present, which is absent
    assert not res.ok and "escalate" in res.note


def test_repair_admission_is_gated_by_reconduction():
    if not HAVE_UCO:
        return
    # a producer that CLAIMS to produce the warrant but its own precondition can't hold -> not chosen
    bad = Step(0, "dog", "wish", warrant="impossible_fact", produces="confirmed_owl(forest)")
    res = repair(_bark(), World(), producers=[bad])
    assert not res.ok                                  # nothing conductable -> no unsound admission


def test_repair_diagnosis_does_not_mutate_world():
    if not HAVE_UCO:
        return
    w = World()                                        # empty: bark blocks, nothing producible
    before = set(w.facts)
    repair(_bark(), w, producers=[_SEE])
    assert w.facts == before                           # a failed repair left the world untouched


def test_repair_with_circuit_producer():
    if not HAVE_UCO:
        return
    see_circuit = lift(extrude("See", "Canine", [
        FlowStep("dog", "see", warrant="owl_present(forest)", produces="confirmed_owl(forest)", passed=True)]))
    w = World(); w.close("owl_present(forest)")
    res = repair(_bark(), w, producers=[see_circuit])  # splice a whole sub-CIRCUIT to re-establish the warrant
    assert res.ok and w.warrants("near(dog,owl)")
