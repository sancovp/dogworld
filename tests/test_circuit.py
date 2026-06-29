import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, extrude
from dogworld.circuit import HAVE_UCO, lift, detect, give_circuit

_FLOW = [
    FlowStep("dog", "move", place="forest", passed=True),
    FlowStep("dog", "see", warrant="owl_present(forest)", produces="confirmed_owl(forest)",
             place="forest", passed=True),
    FlowStep("dog", "bark", warrant="confirmed_owl(forest)", produces="near(dog,owl)",
             place="forest", passed=True),
]


def _circuit():
    return lift(extrude("Confirm-then-bark", "Canine", _FLOW, tags=("owl",)))


def test_terminals_inferred():
    if not HAVE_UCO:
        return
    c = _circuit()
    # input = warrant consumed but not produced inside; output = produced but not consumed inside
    assert c.inputs == {"owl_present(forest)"}
    assert c.outputs == {"near(dog,owl)"}
    assert "confirmed_owl(forest)" not in c.inputs and "confirmed_owl(forest)" not in c.outputs  # internal coupling


def test_conduct_success_when_input_terminal_holds():
    if not HAVE_UCO:
        return
    from uco import LinkStatus
    w = World(); w.close("owl_present(forest)")
    r = _circuit().conduct(w)
    assert r.status == LinkStatus.SUCCESS
    assert w.warrants("near(dog,owl)")                 # the output terminal got produced


def test_conduct_blocked_at_unwarranted_junction():
    if not HAVE_UCO:
        return
    from uco import LinkStatus
    c = _circuit()
    r = c.conduct(World())                              # input terminal missing
    assert r.status == LinkStatus.BLOCKED               # sound conduction — can't pass an unwarranted junction
    assert "owl_present(forest)" in r.error
    assert not c.conducts(World())


def test_circuit_chain_is_a_uco_link_homoiconic():
    if not HAVE_UCO:
        return
    from uco import Link
    assert isinstance(_circuit().chain, Link)           # a Chain IS a Link -> Circuit-of-Circuits closes


def test_detect_shared_motif():
    if not HAVE_UCO:
        return
    s1 = extrude("Confirm-then-bark", "Canine", _FLOW)
    s2 = extrude("See-then-bark", "Canine", _FLOW[1:])  # shares the see->bark sub-path
    motifs = detect([s1, s2])
    assert motifs and [s.action for s in motifs[0]] == ["see", "bark"]


def test_dogfood_give_circuit_to_agent():
    if not HAVE_UCO:
        return
    from uco import LinkStatus
    class Owlish:  # any object
        name = "owl"
    owl = Owlish()
    c = _circuit()
    give_circuit(owl, c)
    assert owl.circuits == [c]
    w = World(); w.close("owl_present(forest)")
    assert owl.circuits[0].conduct(w).status == LinkStatus.SUCCESS
