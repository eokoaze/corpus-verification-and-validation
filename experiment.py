"""
Dose-response experiment, run under BOTH smoothing schemes so they can be compared:
  - add-k (Lidstone), the standard baseline smoothing, k configurable
  - RGT (Reciprocal Good-Turing), parameter-free
plus the frequency-difference baseline measure.
"""
from __future__ import annotations
import random, json, time, sys
from collections import Counter

from metric import (tokenize, ngram_counts, jensen_shannon_fast as jsd_addk,
                    token_freq_baseline)
from rgt import jsd_rgt
from defects import to_documents, INJECTORS, inject_foreign

CLEAN_ENGLISH = ["pride_prejudice", "sherlock", "tale_two_cities",
                 "great_expect", "dubliners", "moby_dick"]
RATES = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]
SEEDS = list(range(10))

DEFECT_CONFIG = {
    "duplicate":   {"level": "word",  "kwargs": {}},
    "truncate":    {"level": "word",  "kwargs": {"keep_tokens": 5}},
    "boilerplate": {"level": "word",  "kwargs": {}},
    "foreign":     {"level": "char3", "kwargs": {}},
    "encoding":    {"level": "char3", "kwargs": {"char_rate": 0.15}},
}


def load(name):
    return open(f"corpora/{name}.txt", encoding="utf-8").read()


def char_ngram_counts(text, n=3):
    t = text.lower()
    return Counter(t[i:i + n] for i in range(len(t) - n + 1))


def counts_for(docs, level):
    joined = "\n".join(docs)
    return ngram_counts(tokenize(joined), 1) if level == "word" else char_ngram_counts(joined, 3)


def split_docs(name, target=200, seed=0):
    docs = to_documents(load(name), target)
    rng = random.Random(seed)
    rng.shuffle(docs)
    mid = len(docs) // 2
    return docs[:mid], docs[mid:]


def build_cache():
    cache = {}
    for corpus in CLEAN_ENGLISH:
        for seed in SEEDS:
            ref, test = split_docs(corpus, 200, seed=seed)
            cache[(corpus, seed)] = {
                "test": test,
                "ref_word": counts_for(ref, "word"),
                "ref_char3": counts_for(ref, "char3"),
            }
    return cache


def run_defect(defect, cache, arabic_docs):
    cfg = DEFECT_CONFIG[defect]; level = cfg["level"]; injector = INJECTORS[defect]
    refkey = "ref_word" if level == "word" else "ref_char3"
    out = {r: {"rgt": [], "addk": [], "baseline": []} for r in RATES}
    for corpus in CLEAN_ENGLISH:
        for seed in SEEDS:
            e = cache[(corpus, seed)]
            rc = e[refkey]; test = e["test"]
            for r in RATES:
                rng = random.Random(seed * 1000 + int(r * 100))
                if defect == "foreign":
                    dtest = inject_foreign(test, r, rng, foreign_pool=arabic_docs)
                else:
                    dtest = injector(test, r, rng, **cfg["kwargs"])
                tc = counts_for(dtest, level)
                out[r]["rgt"].append(jsd_rgt(rc, tc))
                out[r]["addk"].append(jsd_addk(rc, tc, k=0.1))
                out[r]["baseline"].append(token_freq_baseline(rc, tc))
    return out


if __name__ == "__main__":
    only = sys.argv[1:] or list(DEFECT_CONFIG)
    t0 = time.time()
    cache = build_cache()
    arabic_docs = to_documents(load("arabic_quran"), 200)
    print(f"cache built in {time.time()-t0:.1f}s", flush=True)
    try:
        results = json.load(open("results_both.json"))
    except FileNotFoundError:
        results = {}
    for defect in only:
        if defect in results:
            print(f"skip {defect}"); continue
        t = time.time()
        r = run_defect(defect, cache, arabic_docs)
        results[defect] = {str(k): v for k, v in r.items()}
        json.dump(results, open("results_both.json", "w"))
        print(f"{defect}: {time.time()-t:.1f}s (saved)", flush=True)
    print(f"TOTAL {time.time()-t0:.1f}s", flush=True)
