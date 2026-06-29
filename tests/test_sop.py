import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World
from dogworld.sop import FlowStep, extrude, replay, SOPStore

FLOW = [
    FlowStep("dog", "move", warrant="", place="yard", passed=True),
    FlowStep("dog", "bark-in-yard", warrant="confirmed_owl(yard)", place="yard", passed=False),  # slop
    FlowStep("dog", "see", warrant="owl_present(forest)", place="forest", passed=True),
    FlowStep("dog", "bark", warrant="confirmed_owl(forest)", place="forest", passed=True),
]


def _sop():
    return extrude("Confirm-then-bark", "Canine", FLOW, subdomain="Alerting",
                   tags=["owl", "bark"], fitness=2,
                   input_signature={"place": {"example": "forest", "required": True}})


def test_extrude_keeps_only_warranted_steps():
    sop = _sop()
    assert len(sop.steps) == 3                       # the unwarranted yard bark is dropped
    assert all("yard" not in s.action or s.action == "move" for s in sop.steps)
    assert [s.order for s in sop.steps] == [1, 2, 3]  # re-ordered after filtering
    assert sop.slug == "confirm-then-bark"


def test_replay_ok_when_warrants_hold():
    w = World(); w.close("owl_present(forest)"); w.close("confirmed_owl(forest)")
    r = replay(_sop(), w)
    assert r.ok and r.stale_at is None


def test_replay_stale_when_world_changed():
    w = World(); w.close("owl_present(forest)")       # confirmed_owl(forest) NOT closed
    r = replay(_sop(), w)
    assert not r.ok
    assert r.stale_at == 3                             # the bark step's warrant no longer holds
    assert "confirmed_owl(forest)" in r.reason


def test_store_save_search_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        store = SOPStore(tmp)
        store.save(_sop())
        names = [s.name for s in store.search("bark owl")]
        assert "Confirm-then-bark" in names
        assert store.search("kubernetes deployment") == []   # irrelevant query -> no hits


def test_ungated_move_step_is_not_revalidated():
    # the move step has no warrant -> replay never marks it stale
    w = World(); w.close("owl_present(forest)"); w.close("confirmed_owl(forest)")
    assert replay(_sop(), w).ok
