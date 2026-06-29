"""sdt — the informative-percept channel. What makes CALIBRATION possible.

Blind soft-RNG firing can't be calibrated (a perception that fires independently of ground truth
has no interior optimum). Calibration needs the percept to CARRY INFORMATION about the world: the
world emits a noisy signal correlated with truth, and the agent decides on its strength. That makes
the agent a signal detector with a computable d' and an interior optimal threshold.

Equal-variance Gaussian SDT:
  signal | owl present  ~  N(d', 1)
  signal | owl absent   ~  N(0,  1)
  the agent barks iff signal > tau.   Sweep tau -> the ROC; the net-reward-optimal tau is interior.

This module is pure math (Channel, Detector, recovered d', optimal criterion). The integrated
world run (gate + WISDOM + catalysis as the actual reward) lives in examples/sdt_evolve.py.
Stdlib only; no API, no external DB.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Channel:
    """The world's noisy observation channel. d_prime = how separable owl-present is from absent."""
    d_prime: float = 1.5

    def emit(self, present: bool, rng: random.Random) -> float:
        return rng.gauss(self.d_prime if present else 0.0, 1.0)


@dataclass
class Detector:
    """An agent's decision policy: bark iff the percept exceeds the agent's threshold tau.
    Low tau = eager (more hits AND more false alarms); high tau = skeptical (fewer of both)."""
    tau: float

    def fires(self, signal: float) -> bool:
        return signal > self.tau


# ── inverse normal CDF (Acklam's rational approximation) — for z-scores / d' recovery ──
def _ndtri(p: float) -> float:
    if p <= 0.0:
        return -math.inf
    if p >= 1.0:
        return math.inf
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def recovered_dprime(hit_rate: float, fa_rate: float) -> float:
    """Estimate d' from observed hit / false-alarm rates: d' = z(HR) - z(FAR). Validates the channel."""
    hr = min(max(hit_rate, 1e-4), 1 - 1e-4)
    far = min(max(fa_rate, 1e-4), 1 - 1e-4)
    return _ndtri(hr) - _ndtri(far)


def optimal_threshold(d_prime: float, base_rate: float, value: float = 1.0,
                      fa_cost: float = 1.0, miss_cost: float = 1.0) -> float:
    """The reward-optimal criterion (signal units) for equal-variance Gaussian SDT.

    x_c = d'/2 + (1/d') ln(beta),  beta = [P(absent)·fa_cost] / [P(present)·(value+miss_cost)].
    As false alarms get costlier (or owls rarer), beta rises and the optimal tau rises (be skeptical).
    """
    if d_prime <= 0:
        return math.inf  # no information -> no informative threshold (can't calibrate)
    p_present = max(min(base_rate, 1 - 1e-9), 1e-9)
    beta = ((1 - p_present) * fa_cost) / (p_present * (value + miss_cost))
    return d_prime / 2 + (1.0 / d_prime) * math.log(beta)
