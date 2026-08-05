"""
Document-level detection for STRUCTURAL (verification) defects.

Hypothesis from the dose-response results:
  Corpus-level divergence (a VALIDATION instrument) is weak for duplication and
  truncation, because those defects barely shift the aggregate n-gram
  distribution. They are structural defects and must be detected at the
  DOCUMENT level -- exactly the verification/validation split the source paper
  argues for.

Detectors (all information-theoretic / compression-flavoured):
  duplicate : pairwise JS distance between documents; near-zero => duplicate.
              Cheap proxy: hash + minhash-free exact JSD on shortlist.
  truncate  : document length in tokens; and compression codelength per token
              (very short docs have anomalous codelength/token).
  boilerplate: repeated-line frequency within/between docs.

We evaluate as CLASSIFICATION with ground-truth labels (we know which document
indices we corrupted), reporting ROC-AUC and precision/recall at a threshold.
"""
from __future__ import annotations
import random
import json
import statistics as st
from collections import Counter

from metric import tokenize, ngram_counts
from rgt import jsd_rgt as jsd
from defects import to_documents, _pick_indices
from experiment import load, split_docs

RATES = [0.05, 0.10, 0.20]
SEEDS = list(range(10))
CORPORA = ["pride_prejudice", "sherlock", "tale_two_cities",
           "great_expect", "dubliners", "moby_dick"]


# ---------- labelled injection (returns defect indices = ground truth) --------

def inject_duplicate_labelled(docs, rate, rng):
    """
    Replace `rate` fraction of docs with copies of other docs.
    Ground truth = ALL documents that are non-unique afterwards (both the copy
    and its source), because a duplicate detector legitimately flags both
    members of a duplicate pair; penalising it for flagging the source would
    understate its true performance.
    """
    docs = list(docs)
    idx = _pick_indices(len(docs), rate, rng)
    for i in idx:
        src = rng.randrange(len(docs))
        while src == i and len(docs) > 1:
            src = rng.randrange(len(docs))
        docs[i] = docs[src]
    # ground truth: every document whose text appears more than once
    text_counts = Counter(docs)
    dup_idx = {i for i, d in enumerate(docs) if text_counts[d] > 1}
    return docs, dup_idx


def inject_truncate_labelled(docs, rate, rng, keep_tokens=5):
    docs = list(docs)
    idx = _pick_indices(len(docs), rate, rng)
    for i in idx:
        docs[i] = " ".join(docs[i].split()[:keep_tokens])
    return docs, idx


# ---------- document-level scores (higher = more suspicious) ------------------

def score_duplicate(docs, shortlist=25):
    """
    Suspicion = 1 - (min JS distance to any other doc).

    Two-stage for tractability (and this is what a real pipeline does):
      1. Exact-hash prefilter: identical text => distance 0 => score 1.0.
      2. For the rest, compare only against a `shortlist` of documents with the
         most similar length (near-duplicates have similar length), which bounds
         the pairwise cost while preserving detection of near-duplicates.
    """
    n = len(docs)
    scores = [0.0] * n

    # stage 1: exact duplicates
    by_text = {}
    for i, d in enumerate(docs):
        by_text.setdefault(d, []).append(i)
    exact = set()
    for _, idxs in by_text.items():
        if len(idxs) > 1:
            for i in idxs:
                scores[i] = 1.0
                exact.add(i)

    # stage 2: near-duplicate check on the remainder, length-bucketed shortlist
    rest = [i for i in range(n) if i not in exact]
    if len(rest) > 1:
        counts = {i: ngram_counts(tokenize(docs[i]), 1) for i in rest}
        order = sorted(rest, key=lambda i: len(docs[i]))
        pos = {i: p for p, i in enumerate(order)}
        for i in rest:
            p = pos[i]
            lo, hi = max(0, p - shortlist // 2), min(len(order), p + shortlist // 2)
            best = 1.0
            for j in order[lo:hi]:
                if j == i:
                    continue
                v = jsd(counts[i], counts[j])
                if v < best:
                    best = v
            scores[i] = 1.0 - best
    return scores


def score_truncate(docs):
    """Suspicion = 1/(1+tokens): very short docs score near 1."""
    return [1.0 / (1.0 + len(d.split())) for d in docs]


# ---------- evaluation --------------------------------------------------------

def roc_auc(scores, labels):
    """AUC via rank statistic (Mann-Whitney U). labels: 1=defective."""
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return float("nan")
    # rank-based
    allv = sorted(zip(scores, labels))
    ranks = {}
    i = 0
    r = 1
    vals = [s for s, _ in allv]
    # average ranks for ties
    import itertools
    rank_of = {}
    idx = 0
    while idx < len(vals):
        j = idx
        while j + 1 < len(vals) and vals[j + 1] == vals[idx]:
            j += 1
        avg = (idx + 1 + j + 1) / 2
        for k in range(idx, j + 1):
            rank_of[k] = avg
        idx = j + 1
    sum_pos_ranks = sum(rank_of[k] for k, (_, l) in enumerate(allv) if l == 1)
    n1, n0 = len(pos), len(neg)
    u = sum_pos_ranks - n1 * (n1 + 1) / 2
    return u / (n1 * n0)


def run(defect):
    aucs = {r: [] for r in RATES}
    for corpus in CORPORA:
        for seed in SEEDS:
            _, test = split_docs(corpus, 200, seed=seed)
            for r in RATES:
                rng = random.Random(seed * 977 + int(r * 100))
                if defect == "duplicate":
                    docs, idx = inject_duplicate_labelled(test, r, rng)
                    scores = score_duplicate(docs)
                else:
                    docs, idx = inject_truncate_labelled(test, r, rng)
                    scores = score_truncate(docs)
                labels = [1 if i in idx else 0 for i in range(len(docs))]
                aucs[r].append(roc_auc(scores, labels))
    return {str(r): {"auc_mean": st.mean(v), "auc_sd": st.pstdev(v), "n": len(v)}
            for r, v in aucs.items()}


if __name__ == "__main__":
    out = {}
    for defect in ["truncate", "duplicate"]:
        print(f"running document-level {defect}...", flush=True)
        out[defect] = run(defect)
        print(f"  {defect}: " + "  ".join(
            f"r={r} AUC={v['auc_mean']:.3f}+/-{v['auc_sd']:.3f}"
            for r, v in out[defect].items()), flush=True)
    json.dump(out, open("results_doclevel.json", "w"), indent=2)
