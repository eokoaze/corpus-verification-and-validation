"""
Corrected information-theoretic divergence metric for corpus quality evaluation.

Implements the JSD-based measure specified in METRIC_THEORY.md:
  - add-k (Lidstone) smoothing over the vocabulary union
  - Jensen-Shannon divergence (symmetric, bounded, sqrt is a true metric)
  - per-n-gram pointwise contribution for ranking
  - a token-frequency baseline (the thing the original method implicitly relied on)

All divergences are in BITS (log base 2).
"""
from __future__ import annotations
from collections import Counter
from typing import Iterable, Sequence
import math
import regex as _re

# A token is a letter/digit followed by any letters, digits, or combining marks.
# \p{M} is essential for vocalized Arabic (and Hebrew, Devanagari): diacritics are
# Unicode category Mn, which \w does NOT match, so a naive \w+ pattern silently
# shatters each vocalized word into single letters.
_WORD_RE = _re.compile(r"[\p{L}\p{N}][\p{L}\p{N}\p{M}]*", _re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokenization, Unicode-aware (Latin, Arabic, Cyrillic...)."""
    return _WORD_RE.findall(text.lower())


def ngrams(tokens: Sequence[str], n: int) -> list[tuple[str, ...]]:
    if n <= 0:
        raise ValueError("n must be >= 1")
    if len(tokens) < n:
        return []
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def ngram_counts(tokens: Sequence[str], n: int) -> Counter:
    return Counter(ngrams(tokens, n))


def _smoothed_probs(counts: Counter, vocab: set, N: int, k: float):
    """add-k smoothed probability over the FULL vocab union."""
    V = len(vocab)
    denom = N + k * V
    # every g in vocab gets nonzero mass; g absent from this text -> count 0
    return {g: (counts.get(g, 0) + k) / denom for g in vocab}


def jensen_shannon(counts1: Counter, counts2: Counter, k: float = 0.1) -> float:
    """
    Jensen-Shannon divergence in bits between two n-gram count distributions.
    0 <= JSD <= 1. 0 iff identical distributions.
    """
    vocab = set(counts1) | set(counts2)
    if not vocab:
        return 0.0
    N1 = sum(counts1.values())
    N2 = sum(counts2.values())
    P = _smoothed_probs(counts1, vocab, N1, k)
    Q = _smoothed_probs(counts2, vocab, N2, k)
    jsd = 0.0
    for g in vocab:
        p, q = P[g], Q[g]
        m = 0.5 * (p + q)
        if p > 0:
            jsd += 0.5 * p * math.log2(p / m)
        if q > 0:
            jsd += 0.5 * q * math.log2(q / m)
    # numerical floor
    return max(0.0, jsd)


def js_distance(counts1: Counter, counts2: Counter, k: float = 0.1) -> float:
    """sqrt(JSD): a true metric (satisfies triangle inequality)."""
    return math.sqrt(jensen_shannon(counts1, counts2, k))


def pointwise_contributions(counts1: Counter, counts2: Counter, k: float = 0.1):
    """
    Per-n-gram contribution to JSD (>=0, sums to JSD). For ranking the n-grams
    that drive the divergence — the corrected replacement for |log-ratio| ranking.
    Returns list of (ngram, contribution) sorted descending.
    """
    vocab = set(counts1) | set(counts2)
    N1 = sum(counts1.values())
    N2 = sum(counts2.values())
    P = _smoothed_probs(counts1, vocab, N1, k)
    Q = _smoothed_probs(counts2, vocab, N2, k)
    out = []
    for g in vocab:
        p, q = P[g], Q[g]
        m = 0.5 * (p + q)
        c = 0.0
        if p > 0:
            c += 0.5 * p * math.log2(p / m)
        if q > 0:
            c += 0.5 * q * math.log2(q / m)
        out.append((g, c))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def jensen_shannon_fast(counts1: Counter, counts2: Counter, k: float = 0.1) -> float:
    """Vectorized JSD (numpy) — identical result to jensen_shannon, much faster."""
    import numpy as np
    vocab = set(counts1) | set(counts2)
    if not vocab:
        return 0.0
    vocab = list(vocab)
    N1 = sum(counts1.values()); N2 = sum(counts2.values())
    V = len(vocab)
    c1 = np.fromiter((counts1.get(g, 0) for g in vocab), dtype=np.float64, count=V)
    c2 = np.fromiter((counts2.get(g, 0) for g in vocab), dtype=np.float64, count=V)
    p = (c1 + k) / (N1 + k * V)
    q = (c2 + k) / (N2 + k * V)
    m = 0.5 * (p + q)
    jsd = 0.5 * np.sum(p * np.log2(p / m)) + 0.5 * np.sum(q * np.log2(q / m))
    return float(max(0.0, jsd))


def token_freq_baseline(counts1: Counter, counts2: Counter) -> float:
    """
    Baseline the paper implicitly relied on: mean absolute difference of
    relative frequencies over the shared vocabulary union (L1 / total variation
    style). Intentionally simple and unweighted-by-information.
    """
    vocab = set(counts1) | set(counts2)
    if not vocab:
        return 0.0
    N1 = sum(counts1.values()) or 1
    N2 = sum(counts2.values()) or 1
    return sum(abs(counts1.get(g, 0) / N1 - counts2.get(g, 0) / N2)
               for g in vocab) / len(vocab)


def evaluate_pair(text1: str, text2: str, n: int = 1, k: float = 0.1) -> dict:
    """Convenience: full comparison of two raw texts at n-gram order n."""
    t1, t2 = tokenize(text1), tokenize(text2)
    c1, c2 = ngram_counts(t1, n), ngram_counts(t2, n)
    return {
        "n": n,
        "jsd_bits": jensen_shannon(c1, c2, k),
        "js_distance": js_distance(c1, c2, k),
        "baseline_l1": token_freq_baseline(c1, c2),
        "tokens_1": len(t1),
        "tokens_2": len(t2),
        "types_1": len(c1),
        "types_2": len(c2),
    }


if __name__ == "__main__":
    # sanity: identical text -> 0 ; disjoint -> near max
    a = "the quick brown fox jumps over the lazy dog " * 50
    b = "the quick brown fox jumps over the lazy dog " * 50
    c = "zzz yyy xxx www vvv uuu ttt sss rrr qqq " * 50
    print("identical  JSD =", round(jensen_shannon(ngram_counts(tokenize(a),1),
                                                    ngram_counts(tokenize(b),1)), 6))
    print("disjoint   JSD =", round(jensen_shannon(ngram_counts(tokenize(a),1),
                                                    ngram_counts(tokenize(c),1)), 6))
