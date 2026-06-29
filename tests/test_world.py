import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World


def test_close_and_warrants():
    w = World()
    ok, _ = w.close("owl_hooted@1")
    assert ok and w.warrants("owl_hooted@1")
    assert not w.warrants("owl_hooted@2")


def test_negation_contradiction():
    w = World()
    assert w.close("near(dog,owl)")[0]
    ok, reason = w.close("!near(dog,owl)")
    assert not ok and "negation" in reason
    # and the reverse order
    w2 = World()
    assert w2.close("!rain")[0]
    assert not w2.close("rain")[0]


def test_functional_contradiction():
    w = World()
    w.declare_functional("at", subject_arity=1)
    assert w.close("at(dog,barn)")[0]
    ok, reason = w.close("at(dog,field)")   # dog can be at one place
    assert not ok and "functional" in reason
    assert w.close("at(dog,barn)")[0]       # idempotent re-close of the same value is fine
    assert w.close("at(cat,field)")[0]      # different subject is fine


def test_consistent_with_is_pure():
    w = World()
    w.close("near(dog,owl)")
    ok, _ = w.consistent_with("!near(dog,owl)")
    assert not ok
    # consistent_with must not mutate
    assert "!near(dog,owl)" not in w.facts
