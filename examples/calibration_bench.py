"""calibration_bench — the measurable: belief vs the certified world.

Two calibrations, both falling out of the soft-RNG-as-prior design:
  1. ACTION calibration: set P(hoot)=p, measure realized hoot frequency -> should track p.
  2. BELIEF calibration: dog.bark fires on belief; warranted-pass rate -> tracks P(hoot)
     (the dog can only be RIGHT as often as the owl actually hoots). WISDOM bleeds at the gap.

This turns 'the dog listens too eagerly relative to reality' into a number. No API calls.

Run: python3 examples/calibration_bench.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, Engine, MockArbiter, RngSpec
from examples.owl_dog import Owl, Dog  # reuse the agents


def run(p_hoot: float, p_bark: float, ticks: int, seed: int = 1):
    world, stats = World(), Stats(values={"WISDOM": 1000})  # big pool so it doesn't floor
    owl, dog = Owl(), Dog()
    owl.set_rng_values("hoot", p=p_hoot)
    dog.set_rng_values("bark", p=p_bark)
    report = Engine(world, [owl, dog], stats=stats, arbiter=MockArbiter(seed)).run(ticks)
    realized_hoot = report.fires.get("hoot", 0) / ticks
    bark_calib = report.calibration("bark")
    wisdom_lost = stats.count_losses("WISDOM")
    return realized_hoot, bark_calib, wisdom_lost


def main() -> None:
    ticks = 2000
    print(f"{'P(hoot)':>8} {'realized':>9} | {'bark calib':>10} (≈P(hoot)) {'WISDOM lost':>13}")
    for p_hoot in (0.2, 0.5, 0.8):
        realized, bark_calib, lost = run(p_hoot, p_bark=0.7, ticks=ticks)
        print(f"{p_hoot:>8.2f} {realized:>9.3f} | {bark_calib:>10.3f}            {lost:>13}")
    print("\nreading: realized hoot-freq tracks the injected P(hoot) (action calibration);")
    print("bark calibration (warranted/fired) tracks P(hoot) — the dog can only be right as")
    print("often as the owl truly hoots; the rest is WISDOM lost (belief outran the world).")


if __name__ == "__main__":
    main()
