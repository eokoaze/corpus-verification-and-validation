"""
Reciprocal Good-Turing (RGT) smoothing for corpus divergence.

Parameter-free: the reserved mass comes from the Good-Turing singleton estimate,
and is redistributed over the unseen n-grams in proportion to the comparison
partner's distribution there. See RGT_THEORY.md.
"""
from __future__ import annotations
from collections import Counter
import numpy as np

THETA_CAP = 0.5


def gt_theta(counts: Counter, N: int) -> float:
    """Good-Turing estimate of unseen mass: n_1 / N (fraction of singleton types)."""
    if N <= 0:
        return 0.0
    n1 = sum(1 for c in counts.values() if c == 1)
    return n1 / N


def rgt_distributions(counts1: Counter, counts2: Counter):
    """
    Return (vocab, P, Q) as numpy arrays over the vocabulary union, each smoothed
    toward the other by Reciprocal Good-Turing. Both sum to 1.
    """
    vocab = list(set(counts1) | set(counts2))
    V = len(vocab)
    if V == 0:
        return vocab, np.array([]), np.array([])

    N1 = sum(counts1.values())
    N2 = sum(counts2.values())
    c1 = np.fromiter((counts1.get(g, 0) for g in vocab), dtype=np.float64, count=V)
    c2 = np.fromiter((counts2.get(g, 0) for g in vocab), dtype=np.float64, count=V)

    raw1 = c1 / N1 if N1 else np.zeros(V)
    raw2 = c2 / N2 if N2 else np.zeros(V)

    unseen1 = c1 == 0          # in the union but absent from corpus 1
    unseen2 = c2 == 0

    def build(raw_self, raw_partner, unseen_self, counts_self, N_self):
        P = np.empty(V)
        if not unseen_self.any():
            return raw_self.copy()           # nothing to reserve for
        theta = gt_theta(counts_self, N_self)
        theta = max(theta, 1.0 / (N_self + 1.0))   # floor: keep strictly positive
        theta = min(theta, THETA_CAP)              # cap: seen keeps majority mass
        partner_mass = raw_partner[unseen_self].sum()
        P[~unseen_self] = (1.0 - theta) * raw_self[~unseen_self]
        if partner_mass > 0:
            P[unseen_self] = theta * raw_partner[unseen_self] / partner_mass
        else:
            P[unseen_self] = theta / unseen_self.sum()
        return P

    P = build(raw1, raw2, unseen1, counts1, N1)
    Q = build(raw2, raw1, unseen2, counts2, N2)
    return vocab, P, Q


def _jsd_from_pq(P, Q):
    if P.size == 0:
        return 0.0
    M = 0.5 * (P + Q)
    ok = M > 0
    t1 = np.where((P > 0) & ok, P * np.log2(np.divide(P, M, out=np.ones_like(P), where=ok)), 0.0)
    t2 = np.where((Q > 0) & ok, Q * np.log2(np.divide(Q, M, out=np.ones_like(Q), where=ok)), 0.0)
    return float(max(0.0, 0.5 * t1.sum() + 0.5 * t2.sum()))


def jsd_rgt(counts1: Counter, counts2: Counter) -> float:
    """Jensen-Shannon divergence (bits) under RGT smoothing. No free parameter."""
    _, P, Q = rgt_distributions(counts1, counts2)
    return _jsd_from_pq(P, Q)


def js_distance_rgt(counts1: Counter, counts2: Counter) -> float:
    return jsd_rgt(counts1, counts2) ** 0.5


def pointwise_rgt(counts1: Counter, counts2: Counter):
    """Per-n-gram contribution to JSD (>=0, sums to JSD), sorted descending."""
    vocab, P, Q = rgt_distributions(counts1, counts2)
    M = 0.5 * (P + Q)
    ok = M > 0
    t1 = np.where((P > 0) & ok, P * np.log2(np.divide(P, M, out=np.ones_like(P), where=ok)), 0.0)
    t2 = np.where((Q > 0) & ok, Q * np.log2(np.divide(Q, M, out=np.ones_like(Q), where=ok)), 0.0)
    contrib = 0.5 * t1 + 0.5 * t2
    order = np.argsort(-contrib)
    return [(vocab[i], float(contrib[i])) for i in order]


def theta_report(counts: Counter) -> dict:
    """Diagnostic: the data-derived smoothing strength for a corpus."""
    N = sum(counts.values())
    n1 = sum(1 for c in counts.values() if c == 1)
    return {"tokens": N, "types": len(counts), "singletons": n1,
            "theta": gt_theta(counts, N)}


if __name__ == "__main__":
    a = Counter({"the": 100, "cat": 10, "sat": 5, "mat": 1})
    b = Counter({"the": 100, "dog": 10, "ran": 5, "far": 1})
    print("theta A:", round(gt_theta(a, sum(a.values())), 5))
    print("identical:", round(jsd_rgt(a, a), 10))
    print("A vs B:   ", round(jsd_rgt(a, b), 5))
    _, P, Q = rgt_distributions(a, b)
    print("P sums to", round(P.sum(), 10), " Q sums to", round(Q.sum(), 10))
