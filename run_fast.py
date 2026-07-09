"""
Optimized runner: cache reference counts per (corpus, seed, level) once, reuse
across all rates and all defects of that level. Writes each defect to disk on
completion so nothing is lost.
"""
import random, json, time, sys
from collections import Counter
from metric import tokenize, ngram_counts, jensen_shannon_fast as jsd, token_freq_baseline
from defects import to_documents, INJECTORS, inject_foreign
from experiment import (CLEAN_ENGLISH, RATES, SEEDS, DEFECT_CONFIG,
                        load, char_ngram_counts, split_docs)

def counts_for(docs, level):
    joined = "\n".join(docs)
    return ngram_counts(tokenize(joined), 1) if level == "word" else char_ngram_counts(joined, 3)

# Precompute reference counts + test docs once per (corpus, seed)
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
    out = {r: {"jsd": [], "baseline": []} for r in RATES}
    for corpus in CLEAN_ENGLISH:
        for seed in SEEDS:
            entry = cache[(corpus, seed)]
            ref_counts = entry[refkey]; test = entry["test"]
            for r in RATES:
                rng = random.Random(seed * 1000 + int(r * 100))
                if defect == "foreign":
                    dtest = inject_foreign(test, r, rng, foreign_pool=arabic_docs)
                else:
                    dtest = injector(test, r, rng, **cfg["kwargs"])
                tc = counts_for(dtest, level)
                out[r]["jsd"].append(jsd(ref_counts, tc))
                out[r]["baseline"].append(token_freq_baseline(ref_counts, tc))
    return out

if __name__ == "__main__":
    only = sys.argv[1:] or list(DEFECT_CONFIG)
    t0 = time.time()
    print("building cache...", flush=True)
    cache = build_cache()
    arabic_docs = to_documents(load("arabic_quran"), 200)
    print(f"cache built in {time.time()-t0:.1f}s", flush=True)
    results = {}
    try:
        results = json.load(open("results_all.json"))
    except FileNotFoundError:
        pass
    for defect in only:
        if defect in results:
            print(f"skip {defect}"); continue
        t = time.time()
        r = run_defect(defect, cache, arabic_docs)
        results[defect] = {str(k): v for k, v in r.items()}
        json.dump(results, open("results_all.json", "w"))
        print(f"{defect}: {time.time()-t:.1f}s  (saved)", flush=True)
    print(f"TOTAL {time.time()-t0:.1f}s", flush=True)
