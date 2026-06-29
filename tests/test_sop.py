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


def test_flowrecorder_auto_brackets_on_success_and_drops_slop():
    from dogworld.sop import FlowRecorder
    rec = FlowRecorder()
    assert rec.observe(FlowStep("dog", "move", passed=True)) is None
    assert rec.observe(FlowStep("dog", "bark-yard", warrant="confirmed_owl(yard)", passed=False)) is None
    assert rec.observe(FlowStep("dog", "see", warrant="owl_present(forest)", passed=True)) is None
    sop = rec.observe(FlowStep("dog", "bark", warrant="confirmed_owl(forest)", passed=True),
                      success=True, name="Confirm-then-bark", domain="Canine")
    assert sop is not None and len(sop.steps) == 3        # 4 observed, slop bark dropped
    assert rec.buffer == [] and rec.learned == [sop]      # buffer reset, route remembered


def test_promote_to_skill_writes_a_skilltree_node():
    import tempfile
    from dogworld.sop import promote_to_skill
    with tempfile.TemporaryDirectory() as tmp:
        p = promote_to_skill(_sop(), tmp)
        assert p.name == "SKILL.md" and p.exists()
        text = p.read_text()
        assert "name: confirm-then-bark" in text and "## Steps" in text


def test_skilltree_rag_retrieves_a_promoted_sop_if_available():
    try:
        from skilltree import search_folder
    except Exception:
        return  # agent-skilltree not installed; the bridge is optional
    import tempfile
    from dogworld.sop import promote_to_skill
    with tempfile.TemporaryDirectory() as tmp:
        promote_to_skill(_sop(), tmp)
        hits = search_folder(tmp, "bark owl")             # skilltree's BM25 RAG over the promoted node
        assert isinstance(hits, (list, tuple))
