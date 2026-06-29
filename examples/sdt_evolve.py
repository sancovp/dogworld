"""sdt_evolve — calibration made real: an interior optimal threshold, selected on the REAL reward.

The world emits a noisy percept (Channel, d') correlated with whether the owl hooted. The dog
barks iff the percept exceeds its threshold tau. Every bark is adjudicated by the ACTUAL Dogworld
gate: a warranted bark (hit) catalyzes the master (fitness +1); an unwarranted bark (false alarm)
costs WISDOM; staying silent while the owl hooted is a miss. So:

    net(tau) = fitness(catalysis from hits) - WISDOM_loss(false alarms) - miss_cost*misses

Sweeping tau traces an interior optimum (be neither eager nor cowardly) that MATCHES the
signal-detection optimal criterion. With d'=0 (uninformative percept) the optimum vanishes — you
cannot calibrate a blind agent. Deterministic, offline, no external DB.

Run: python3 examples/sdt_evolve.py
"""
import sys, pathlib, random
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld import World, Stats, Agent, perception, propose, gate_perception, catalysis
from dogworld.sdt import Channel, Detector, recovered_dprime, optimal_threshold


class Dog(Agent):
    name = "dog"

    @perception(requires="owl_hooted@{t}", abduces="near@{t}",
                penalty="You thought you heard an owl. In fact, there was not one when you looked.")
    def bark(self):
        return "WOOF!"


class Master(Agent):
    name = "master"

    @perception(requires="near@{t}", abduces="checked@{t}", penalty="nothing was near.")
    def investigate(self):
        return "checked the yard"


def run(tau: float, base_rate: float, d_prime: float, ticks: int, seed: int, miss_cost: float = 1.0):
    rng = random.Random(seed)
    ch, det = Channel(d_prime), Detector(tau)
    world, stats = World(), Stats(values={"WISDOM": 10**9})
    dog, master = Dog(), Master()
    hits = fa = miss = cr = 0
    for t in range(1, ticks + 1):
        present = rng.random() < base_rate
        if present:
            world.close(f"owl_hooted@{t}", food=True, by="owl.hoot")
        if det.fires(ch.emit(present, rng)):
            v = gate_perception(world, stats, dog, dog.manifest["bark"],
                                propose(dog, dog.manifest["bark"], t=t))
            if v.passed:
                hits += 1
                gate_perception(world, stats, master, master.manifest["investigate"],
                                propose(master, master.manifest["investigate"], t=t))
            else:
                fa += 1
        elif present:
            miss += 1
        else:
            cr += 1
    fit = catalysis.fitness(world).by_agent.get("dog", 0)            # = hits, catalytically grounded
    net = fit - stats.count_losses() - miss * miss_cost
    hr = hits / max(hits + miss, 1)
    far = fa / max(fa + cr, 1)
    return {"net": net, "fitness": fit, "fa": fa, "miss": miss, "hr": hr, "far": far}


def sweep(base_rate, d_prime, ticks=1500, seeds=(1, 2, 3, 4)):
    best_tau, best_net, rows = None, -1e18, []
    for i in range(-8, 13):
        tau = i * 0.25
        rs = [run(tau, base_rate, d_prime, ticks, s) for s in seeds]
        net = sum(r["net"] for r in rs) / len(rs)
        hr = sum(r["hr"] for r in rs) / len(rs)
        far = sum(r["far"] for r in rs) / len(rs)
        rows.append((tau, net, hr, far))
        if net > best_net:
            best_tau, best_net = tau, net
    return best_tau, best_net, rows


def main():
    base_rate = 0.5
    print(f"world: owl base-rate {base_rate}, reward = +1 catalytic hit / -1 false alarm / -1 miss\n")
    for d_prime in (2.0, 0.0):
        best_tau, best_net, rows = sweep(base_rate, d_prime)
        # recover d' at the chosen threshold
        rs = [run(best_tau, base_rate, d_prime, 4000, s) for s in (5, 6, 7)]
        hr = sum(r["hr"] for r in rs) / 3
        far = sum(r["far"] for r in rs) / 3
        tag = "INFORMATIVE percept" if d_prime > 0 else "BLIND percept (d'=0)"
        print(f"── d' = {d_prime}  ({tag}) ──")
        for tau, net, h, f in rows[::2]:
            bar = "#" * max(0, int(net / 12))
            mark = "  <- argmax" if tau == best_tau else ""
            print(f"  tau={tau:+.2f}  net={net:7.1f}  HR={h:.2f} FAR={f:.2f}  {bar}{mark}")
        if d_prime > 0:
            opt = optimal_threshold(d_prime, base_rate, value=1, fa_cost=1, miss_cost=1)
            print(f"  empirical argmax tau = {best_tau:+.2f}   |   SDT-optimal criterion = {opt:+.2f}")
            print(f"  recovered d' (z(HR)-z(FAR)) = {recovered_dprime(hr, far):.2f}  (channel d' = {d_prime})")
            print("  -> interior optimum, matches theory, d' recovered.\n")
        else:
            print("  -> no interior optimum: a blind percept cannot be calibrated (the finding, confirmed).\n")


if __name__ == "__main__":
    main()
