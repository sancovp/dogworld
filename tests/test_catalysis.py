import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, Engine, MockArbiter, Agent, perception, RngSpec
from dogworld import catalysis as C
from examples.owl_dog import Owl, Dog


class Master(Agent):
    name = "master"

    @perception(requires="near(dog,owl)", abduces="yard_checked@{t}",
                penalty="nothing was near.", rng=RngSpec(method="always"))
    def investigate(self):
        return "checked"


def _run_chain():
    owl, dog, master = Owl(), Dog(), Master()
    owl.set_rng_method("hoot", "always")
    dog.set_rng_method("bark", "always")
    world = World()
    Engine(world, [owl, dog, master], stats=Stats(), arbiter=MockArbiter(seed=1)).run(1)
    return world, (owl, dog, master)


def test_enablement_edges_recorded():
    world, _ = _run_chain()
    assert "near(dog,owl)" in world.enables.get("owl_hooted@1", set())
    assert "yard_checked@1" in world.enables.get("near(dog,owl)", set())
    assert "owl_hooted@1" in world.food                      # action close = food
    assert "near(dog,owl)" not in world.food                  # perception abduction is NOT food


def test_cat_counts_downstream_structure():
    world, _ = _run_chain()
    assert C.cat(world, "owl_hooted@1") == 2                  # enables near + yard_checked
    assert C.cat(world, "near(dog,owl)") == 1                 # enables yard_checked
    assert C.cat(world, "yard_checked@1") == 0                # leaf: warranted but inert (neutral)


def test_fitness_ranks_the_catalytic_root_highest():
    world, _ = _run_chain()
    fit = C.fitness(world)
    assert fit.by_agent["owl"] == 2 > fit.by_agent["dog"] == 1 > fit.by_agent["master"] == 0
    assert fit.top() == "owl"                                 # the food source grounds the structure


def test_raf_emerges_when_fed_and_collapses_when_starved():
    _, (owl, dog, master) = _run_chain()
    reactions = C.reactions_from_agents([dog, master])
    assert {r.name for r in C.max_raf(reactions, food={"owl_hooted@1"})} == {"dog.bark", "master.investigate"}
    assert C.max_raf(reactions, food=set()) == []             # no food -> no emergence


def test_unwarranted_act_builds_no_structure():
    """bad = decoherence: an unwarranted bark closes nothing, so it adds zero catalysis."""
    from dogworld import gate_perception, propose
    world, stats = World(), Stats()
    dog = Dog()
    gate_perception(world, stats, dog, dog.manifest["bark"], propose(dog, dog.manifest["bark"], t=1))
    assert "near(dog,owl)" not in world.facts
    assert world.enables == {}                                # no enablement edges from a phantom
