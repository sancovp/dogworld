"""owl_dog — the cascade, end to end.

owl.hoot fires (soft prior) and closes a REAL fact (owl_hooted@t). dog.bark fires (soft prior)
on the BELIEF it heard an owl; the gate checks the world:
  - if the owl actually hooted this tick -> WOOF, and near(dog,owl) is abduced backward.
  - if not -> "WISDOM -1: You thought you heard an owl. In fact, there was not one when you
    looked." (returned FROM bark, re-entering context).

Run: python3 examples/owl_dog.py   (MockArbiter, seeded — no API calls)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, Agent, Engine, MockArbiter, RngSpec, action, perception


class Owl(Agent):
    name = "owl"

    @action(rng=RngSpec(values={"p": 0.6}), closes="owl_hooted@{t}")
    def hoot(self):
        return "HOOOO-HOOOO"


class Dog(Agent):
    name = "dog"

    @perception(
        requires="owl_hooted@{t}",
        abduces="near({self},owl)",
        penalty="You thought you heard an owl. In fact, there was not one when you looked.",
        urge="You think you just heard an owl hoot somewhere nearby (felt-strength {p}). "
             "You cannot be certain it was real. If you trust the percept, bark.",
        rng=RngSpec(values={"p": 0.7}),
    )
    def bark(self):
        return "WOOF! (heard the owl -- so it was close enough; near(dog,owl) holds)"


def main() -> None:
    world = World()
    owl, dog = Owl(), Dog()
    engine = Engine(world, [owl, dog], stats=Stats(), arbiter=MockArbiter(seed=7))
    report = engine.run(12)

    print("== cascade (12 ticks) ==")
    for ln in report.lines:
        print(" ", ln)
    print()
    print(report.summary())
    print()
    print(world.dump())


if __name__ == "__main__":
    main()
