import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import Agent, RngSpec, action, perception


class Critter(Agent):
    name = "critter"

    @action(rng=RngSpec(values={"p": 0.6}), closes="did_x@{t}")
    def do_x(self):
        return "x"

    @perception(requires="w@{t}", abduces="a({self})", penalty="nope", rng=RngSpec(values={"p": 0.3}))
    def sense_y(self):
        return "y"

    def undecorated(self):
        return "ignored"


def test_reflection_finds_only_decorated():
    c = Critter()
    assert set(c.manifest) == {"do_x", "sense_y"}      # undecorated method excluded
    assert {m.name for m in c.actions()} == {"do_x"}
    assert {m.name for m in c.perceptions()} == {"sense_y"}


def test_per_instance_rng_isolation():
    a, b = Critter(), Critter()
    a.set_rng_values("do_x", p=0.99)
    assert a.manifest["do_x"].rng.p == 0.99
    assert b.manifest["do_x"].rng.p == 0.6             # not shared across instances


def test_set_rng_method():
    c = Critter()
    c.set_rng_method("sense_y", "always")
    assert c.manifest["sense_y"].rng.p == 1.0
    c.set_rng_method("sense_y", "never")
    assert c.manifest["sense_y"].rng.p == 0.0


def test_urge_rendering_and_templates():
    c = Critter()
    assert "Urge to do_x: 0.60" in c.render_urges()
    assert c.fill("a({self})@{t}", t=5) == "a(critter)@5"
