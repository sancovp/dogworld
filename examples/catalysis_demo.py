"""catalysis_demo — "good" computed: the owl->dog->master alert chain forms a RAF.

owl.hoot (food) ──enables──▶ dog.bark -> near(dog,owl) ──enables──▶ master.investigate -> yard_checked

Each warranted act enables the next's warrant: a Reflexively-Autocatalytic, Food-generated set
grounded in the owl's hoot. We compute the realized catalysis (cat / fitness over what closed)
and the structural RAF (over the reaction network), and show the RAF COLLAPSES with no food =
no owl = no emergence. Deterministic (always-fire), no LLM, no external DB.

Run: python3 examples/catalysis_demo.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, Engine, MockArbiter, Agent, action, perception, RngSpec
from dogworld import catalysis as C
from examples.owl_dog import Owl, Dog


class Master(Agent):
    name = "master"

    @perception(requires="near(dog,owl)", abduces="yard_checked@{t}",
                penalty="You went to check, but the dog was nowhere near anything.",
                urge="Your dog is barking as if something is near (felt-strength {p}). Investigate?",
                rng=RngSpec(method="always"))
    def investigate(self):
        return "master checks the yard (the dog was right -- something was near)"


def main() -> None:
    owl, dog, master = Owl(), Dog(), Master()
    owl.set_rng_method("hoot", "always")        # deterministic: everyone acts
    dog.set_rng_method("bark", "always")

    world = World()
    Engine(world, [owl, dog, master], stats=Stats(), arbiter=MockArbiter(seed=1)).run(1)

    print("== the enablement DAG (catalysis edges) ==")
    for f in sorted(world.enables):
        print(f"  {f}  --enables-->  {sorted(world.enables[f])}")
    print(f"  food (spontaneous, RNG-driven): {sorted(world.food)}")

    print("\n== cat(f) = downstream warranted structure each fact made possible ==")
    for f in sorted(world.facts):
        print(f"  cat({f}) = {C.cat(world, f)}")

    fit = C.fitness(world)
    print("\n== fitness = per-agent catalytic contribution ==")
    for ag, v in sorted(fit.by_agent.items(), key=lambda kv: -kv[1]):
        print(f"  {ag}: {v}")
    print(f"  -> the catalytic ROOT (highest fitness) is '{fit.top()}' — it grounds the whole structure")

    reactions = C.reactions_from_agents([dog, master])
    raf_fed = C.max_raf(reactions, food={"owl_hooted@1"})
    raf_starved = C.max_raf(reactions, food=set())
    print("\n== structural RAF (does the network self-sustain?) ==")
    print(f"  FED   (owl hoots): RAF = {[r.name for r in raf_fed]}   <- EMERGENCE")
    print(f"  STARVED (no owl):  RAF = {[r.name for r in raf_starved]}   <- collapses, no emergence")


if __name__ == "__main__":
    main()
