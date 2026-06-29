"""Offline coverage for the LLM-arbiter + cave-gate paths (fake `complete`, no API calls)."""
import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
_cave = os.environ.get("CAVE_TEAMS_PATH", "")
if os.path.isdir(_cave):
    sys.path.insert(0, _cave)

from dogworld import World, Stats
from dogworld.arbiter import LLMArbiter, _parse_fire
from examples.owl_dog import Dog


def test_parse_fire_robust():
    assert _parse_fire('{"fire": ["bark"]}') == {"bark"}
    assert _parse_fire('```json\n{"fire": ["bark"]}\n```') == {"bark"}
    assert _parse_fire('I will act. {"fire": []}') == set()
    assert _parse_fire('reasoning... \n{"fire":["bark","hoot"]}\n done') == {"bark", "hoot"}


def test_llm_arbiter_with_fake_complete():
    dog = Dog()
    fire_arb = LLMArbiter(complete=lambda s, u: '{"fire": ["bark"]}')
    assert [m.name for m in fire_arb.fired(dog, "perception")] == ["bark"]
    abstain_arb = LLMArbiter(complete=lambda s, u: '{"fire": []}')
    assert abstain_arb.fired(dog, "perception") == []


def test_feedback_accumulates():
    arb = LLMArbiter(complete=lambda s, u: '{"fire": []}')
    arb.add_feedback("dog", "WISDOM -1: no owl")
    assert arb._feedback["dog"] == ["WISDOM -1: no owl"]


def test_cave_gated_turn_warranted_and_penalized():
    try:
        from dogworld.seams import cave_runtime
    except Exception:
        return  # cave-teams not importable in this env; core unaffected
    # always-bark fake arbiter
    arb = LLMArbiter(complete=lambda s, u: '{"fire": ["bark"]}')
    w, s = World(), Stats()
    w.close("owl_hooted@1")                                   # warrant present at t=1
    ctx = cave_runtime.gated_turn(w, s, Dog(), arb, t=1)
    assert ctx["passed"] is True and "WOOF" in ctx["result"]
    assert w.warrants("near(dog,owl)")

    w2, s2 = World(), Stats()                                 # no warrant at t=2
    ctx2 = cave_runtime.gated_turn(w2, s2, Dog(), arb, t=2)
    assert ctx2["passed"] is False and "WISDOM -1" in ctx2["result"]
    assert s2.get("WISDOM") == 9
    assert arb._feedback.get("dog")                           # penalty fed back into context
