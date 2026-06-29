import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, Engine, MockArbiter, RngSpec
from examples.owl_dog import Owl, Dog


def test_cascade_costs_wisdom_for_unwarranted_beliefs():
    w = World()
    eng = Engine(w, [Owl(), Dog()], stats=Stats(), arbiter=MockArbiter(seed=7))
    rep = eng.run(12)
    # some bark fires are warranted (WOOF) and some are not (WISDOM -1)
    assert rep.passes.get("bark", 0) > 0
    assert rep.fails.get("bark", 0) > 0
    assert eng.stats.get("WISDOM") == 10 - rep.fails["bark"]
    assert w.warrants("near(dog,owl)")        # at least one warranted bark abduced proximity


def test_calibration_tracks_world_richness():
    """bark warranted-rate should rise as the owl hoots more (belief can only be as right
    as the world is owl-rich). This is the measurable, deterministic under a fixed seed."""
    def bark_calib(p_hoot):
        owl, dog = Owl(), Dog()
        owl.set_rng_values("hoot", p=p_hoot)
        dog.set_rng_values("bark", p=0.7)
        rep = Engine(World(), [owl, dog], stats=Stats(values={"WISDOM": 10_000}),
                     arbiter=MockArbiter(seed=3)).run(1500)
        return rep.calibration("bark")

    low, high = bark_calib(0.2), bark_calib(0.8)
    assert low < high                                  # more owls -> better-calibrated beliefs
    assert abs(high - 0.8) < 0.07                       # calib tracks P(hoot)
    assert abs(low - 0.2) < 0.07


def test_realized_action_frequency_tracks_prior():
    owl = Owl(); owl.set_rng_values("hoot", p=0.65)
    rep = Engine(World(), [owl], arbiter=MockArbiter(seed=11)).run(2000)
    realized = rep.fires.get("hoot", 0) / 2000
    assert abs(realized - 0.65) < 0.05
