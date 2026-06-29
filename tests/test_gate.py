import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import (World, Stats, Agent, RngSpec, action, perception, propose,
                      gate_perception)

PENALTY = "You thought you heard an owl. In fact, there was not one when you looked."


class Dog(Agent):
    name = "dog"

    @perception(requires="owl_hooted@{t}", abduces="near({self},owl)", penalty=PENALTY)
    def bark(self):
        return "WOOF!"


class Mover(Agent):
    name = "dog"

    @perception(requires="saw_field@{t}", abduces="at({self},field)", penalty="No field in sight.")
    def go_field(self):
        return "trots to the field"


def test_warranted_pass_closes_abduction():
    w, s = World(), Stats()
    dog = Dog()
    w.close("owl_hooted@1")
    v = gate_perception(w, s, dog, dog.manifest["bark"], propose(dog, dog.manifest["bark"], t=1))
    assert v.passed and v.text == "WOOF!"
    assert w.warrants("near(dog,owl)")          # abduced backward, reified on warrant
    assert s.get("WISDOM") == 10                 # no penalty


def test_unwarranted_returns_wisdom_penalty():
    w, s = World(), Stats()
    dog = Dog()
    # nothing hooted at t=1
    v = gate_perception(w, s, dog, dog.manifest["bark"], propose(dog, dog.manifest["bark"], t=1))
    assert not v.passed
    assert v.text == f"WISDOM -1: {PENALTY}"     # literally returned from bark
    assert s.get("WISDOM") == 9
    assert not w.warrants("near(dog,owl)")       # nothing abduced


def test_inconsistent_abduction_is_penalized():
    w, s = World(), Stats()
    w.declare_functional("at", subject_arity=1)
    w.close("at(dog,barn)")                       # the dog is already at the barn
    w.close("saw_field@1")                        # the warrant IS present...
    mover = Mover()
    v = gate_perception(w, s, mover, mover.manifest["go_field"],
                        propose(mover, mover.manifest["go_field"], t=1))
    # warrant present but abduced at(dog,field) contradicts at(dog,barn) -> penalty (B)
    assert not v.passed and "inconsistent" in v.reason
    assert s.get("WISDOM") == 9
    assert not w.warrants("at(dog,field)")
