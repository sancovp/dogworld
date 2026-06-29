import sys, pathlib, random
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dogworld.sdt import Channel, Detector, recovered_dprime, optimal_threshold
from examples.sdt_evolve import sweep


def test_channel_separates_present_from_absent():
    rng = random.Random(0)
    ch = Channel(d_prime=2.0)
    present = sum(ch.emit(True, rng) for _ in range(2000)) / 2000
    absent = sum(ch.emit(False, rng) for _ in range(2000)) / 2000
    assert present - absent > 1.5            # ~ d'


def test_detector_threshold():
    d = Detector(tau=0.5)
    assert d.fires(0.6) and not d.fires(0.4)


def test_recovered_dprime_matches():
    # HR=0.8413 (z=+1), FAR=0.1587 (z=-1) -> d' ~ 2.0
    assert abs(recovered_dprime(0.8413, 0.1587) - 2.0) < 0.1


def test_optimal_threshold_theory_and_monotonicity():
    # d'=2, base=0.5, equal costs -> x_c = 1 + 0.5*ln(0.5) ~ 0.653
    assert abs(optimal_threshold(2.0, 0.5, 1, 1, 1) - 0.653) < 0.01
    # rarer owls -> be more skeptical (higher tau)
    assert optimal_threshold(2.0, 0.1) > optimal_threshold(2.0, 0.5)
    # costlier false alarms -> higher tau
    assert optimal_threshold(2.0, 0.5, fa_cost=5) > optimal_threshold(2.0, 0.5, fa_cost=1)
    # no information -> no informative threshold
    assert optimal_threshold(0.0, 0.5) == float("inf")


def test_informative_percept_has_interior_optimum():
    best_tau, _, rows = sweep(0.5, 2.0, ticks=900, seeds=(1, 2))
    taus = [r[0] for r in rows]
    assert min(taus) < best_tau < max(taus)            # strictly interior
    assert abs(best_tau - optimal_threshold(2.0, 0.5, 1, 1, 1)) < 0.4   # near theory


def test_blind_percept_cannot_be_calibrated():
    best_tau, _, rows = sweep(0.5, 0.0, ticks=900, seeds=(1, 2))
    # net declines monotonically as tau rises -> optimum is at the low extreme, not interior
    assert best_tau <= rows[1][0]
