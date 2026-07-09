# Ground-Truth Results Memo
**Status: Tier-2 ground truth ESTABLISHED.** These are the empirical claims the
IEEE paper can now make and defend. Everything below is reproducible from this
repo (`metric.py`, `defects.py`, `run_fast.py`, `doclevel.py`).

---

## 1. Experimental design

**Substrate.** 9 license-clean corpora (~3M words): 6 public-domain English
novels, the King James Bible (archaic register), the Arabic Qur'an (non-Latin
script). Gutenberg boilerplate stripped and verified absent.

**Protocol.** Each corpus is split by document into a trusted REFERENCE half and
a TEST half. A defect is injected into the TEST half at a controlled rate
r ∈ {0, .05, .10, .15, .20, .30, .40, .50}. Because we control the injection,
the correct answer is known — this is the ground truth the source draft lacked.

**Scale.** 6 corpora × 10 seeds = 60 independent measurements per (defect, rate)
cell; 5 defect types; 8 rates. Document-level experiments: 60 runs × 3 rates.

**Metric.** Jensen–Shannon divergence (bits), add-k smoothed over the vocabulary
union. **Baseline.** Mean absolute difference of relative frequencies — the
frequency-counting approach the original draft implicitly relied on.

**n-gram level is chosen per defect** (a finding, not an assumption — see §4.1):
word unigrams for structural defects, character trigrams for script/encoding.

---

## 2. Metric properties (verified empirically, not merely asserted)

| Property | Result |
|---|---|
| Symmetry JSD(P,Q)=JSD(Q,P) | holds |
| Boundedness 0 ≤ JSD ≤ 1 bit | holds |
| Identity JSD(P,P)=0 | holds |
| Triangle inequality for √JSD | 60/60 checks, 0 violations |

Consequence: **"distance metric" is now a defensible claim** (√JSD is a true
metric). The draft asserted this of a quantity that was neither KL divergence
nor a metric. The zero-frequency problem — listed as an open limitation in the
draft — is **dissolved** by smoothing over the vocabulary union.

## 3. Reproduction of the draft's central claim on independent data

|                        | word-JSD | char3-JSD |
|------------------------|---------|-----------|
| clean English vs English | 0.16  | 0.06 |
| English vs KJV Bible     | 0.33  | 0.15 |
| English vs Arabic        | 0.99  | 0.99 |

The ~2× jump from related→archaic mirrors the draft's 0.84→1.84 pattern, now on
a principled bounded scale, and the cross-script case saturates at the 1-bit
ceiling. The method is script-agnostic, as the draft claimed but never tested.

---

## 4. HEADLINE RESULTS

### 4.1 Dose-response: JSD is monotonic in defect rate for all five defects

Mean JSD (n=60/cell):

| defect | r=0 | r=.05 | r=.10 | r=.20 | r=.30 | r=.50 | monotonic |
|---|---|---|---|---|---|---|---|
| foreign     | 0.012 | 0.038 | 0.063 | 0.128 | 0.178 | 0.318 | **1.00** |
| encoding    | 0.012 | 0.018 | 0.025 | 0.040 | 0.055 | 0.089 | **1.00** |
| duplicate   | 0.062 | 0.064 | 0.066 | 0.069 | 0.073 | 0.079 | 1.00 |
| boilerplate | 0.062 | 0.064 | 0.066 | 0.069 | 0.073 | 0.080 | 1.00 |
| truncate    | 0.062 | 0.063 | 0.064 | 0.066 | 0.068 | 0.075 | 1.00 |

### 4.2 THE KEY RESULT: the frequency baseline fails where JSD succeeds

Clean (r=0) vs lightly-defective (r=0.05), Mann–Whitney one-sided, n=60/group:

| defect | JSD p | JSD d | baseline p | baseline d | baseline verdict |
|---|---|---|---|---|---|
| foreign  | 3.95e-21 | **+2.34** | 7.94e-03 | +0.42 | detects, 5.5× weaker |
| encoding | 2.92e-12 | **+1.42** | **1.000** | **−0.80** | **FAILS — wrong direction** |

On encoding corruption the baseline is **non-monotonic** (only 0.57 of rate-steps
increase) and its effect size is **negative**: it reports a *more corrupted*
corpus as *more similar* to the clean reference. JSD detects it at p ≈ 3×10⁻¹².
This single result justifies the information-theoretic framing.
(See `fig_baseline_failure.pdf`.)

### 4.3 The verification/validation split is empirically real

At corpus level, the three structural defects are **not** detected by either
metric at r=0.05 (all p > 0.11, d ≤ 0.10). Moved to the **document level**, they
are detected perfectly:

| defect | corpus-level d (r=.05) | document-level ROC-AUC |
|---|---|---|
| truncate  | 0.06 (n.s.) | **1.000 ± 0.000** |
| duplicate | 0.10 (n.s.) | **1.000 ± 0.000** |

(AUC at r = .05, .10, .20; 60 runs each.)

**Interpretation — this is the paper's theoretical payoff.** Structural
(*verification*) defects are invisible to aggregate distributional comparison
and require document-level instruments; content (*validation*) defects are
exactly what corpus-level divergence detects. The draft's verification/validation
distinction, argued only philosophically, turns out to predict *which instrument
works*. That converts a taxonomy into a testable, confirmed claim.

### 4.4 Robustness

Monotonicity holds for every smoothing value k ∈ {0.01, 0.1, 0.5, 1.0} on both
content defects. The result is not an artifact of the smoothing parameter.

---

## 5. Bugs caught during this phase (and why they matter for the paper)

1. **Document-splitter bug.** `to_documents()` split only on blank lines; the
   Qur'an is one verse per newline, so it returned **1 document of 706,471 chars**
   instead of ~200. Every foreign-contamination injection was inserting the whole
   Qur'an (114× an English document). It produced a huge, beautiful, *invalid*
   signal (JSD ≈ 0.96 at r=0.25 vs the true 0.088). Fixed; all results re-run.
2. **Mislabelled corpus.** GITenberg "War and Peace" is an *English translation*
   (0 Cyrillic codepoints). The metric correctly scored it as English; my label
   was wrong. Replaced with genuine Arabic.
3. **Mislabelled ground truth.** Duplicate detection scored AUC 0.947 until the
   labels were corrected to mark *both* members of a duplicate pair (a detector
   legitimately flags both). True AUC = 1.000.

These belong in the paper. Each is exactly the class of defect the paper argues
V&V must catch, and #1 in particular demonstrates the thesis: **a preprocessing
bug masqueraded as a finding.**

---

## 6. What the paper can now claim

1. A corrected, formally-grounded divergence metric (symmetric, bounded, √ is a
   true metric, no zero-frequency problem) — replacing an ad-hoc measure
   mis-identified as relative entropy.
2. The first controlled defect-injection ground truth for corpus V&V, with
   dose-response curves and significance tests over 2,400+ measurements.
3. Evidence that the frequency baseline *fails outright* (wrong sign) on encoding
   corruption, where the information-theoretic metric succeeds.
4. Empirical confirmation that the verification/validation distinction predicts
   the correct detection instrument (document-level vs corpus-level).
5. Script-agnostic behaviour demonstrated on Arabic, not merely asserted.

## 7. Deliverables in this repo
- `METRIC_THEORY.md` — derivation + why the draft's formulation was wrong
- `metric.py` — corrected metric (exact + vectorized), baseline
- `defects.py` — injection harness (5 defect types + parallel misalignment)
- `run_fast.py`, `experiment.py` — dose-response driver (cached)
- `doclevel.py` — document-level detectors + ROC-AUC
- `figures.py` → `fig_dose_response.pdf`, `fig_baseline_failure.pdf`
- `results_all.json`, `results_doclevel.json`, `summary_table.json`
