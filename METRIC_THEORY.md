# Corrected Divergence Metric — Theory Specification

## 1. What the original paper defined (and why it's wrong)

The draft defines, for an n-gram `g` occurring in both texts T1 and T2:

    P_T(g) = C_T(g) / N_T                          (frequency estimate)
    H_T(g) = -log2 P_T(g)                          ("entropy" of the n-gram)
    D(g)   = |H_T1(g) - H_T2(g)| = |log2 P_T1(g) - log2 P_T2(g)|
    E_{C1,C2} = (1/n) * sum_i D(g_i)               (over shared n-grams only)

Problems:
1. Called "relative entropy" / KL divergence. It is NOT. KL is
   D_KL(P||Q) = sum_x P(x) log(P(x)/Q(x)) — probability-weighted, asymmetric.
   The draft's D is an UNWEIGHTED mean of absolute log-ratios. A rare n-gram
   (huge |log-ratio|) counts as much as a dominant one.
2. Called a "distance metric" with no proof of the metric axioms.
3. Restricted to the INTERSECTION of vocabularies — discards the most
   diagnostic signal (n-grams present in one corpus, absent in the other),
   the "zero-frequency problem" it then lists as a limitation.
4. MLE probabilities C(g)/N are undefined (log 0) for unseen n-grams, which is
   exactly WHY it was forced onto the intersection.

## 2. Corrected formulation

We ground the measure in cross-entropy / KL divergence with proper smoothing,
so it is (a) theoretically named correctly, (b) defined over the FULL vocabulary
union, (c) symmetric by construction.

### 2.1 Smoothed probability model
Use add-k (Lidstone) smoothing over the shared vocabulary union V = V1 ∪ V2,
with vocabulary size |V| and per-text token count N_T:

    P_T(g) = (C_T(g) + k) / (N_T + k*|V|)          k = 0.1 default (tunable)

This assigns nonzero probability to every g in V for both texts, dissolving the
zero-frequency problem instead of side-stepping it. (We will also report a
Kneser-Ney variant as a robustness check.)

### 2.2 Jensen-Shannon divergence (primary metric)
JSD is the correct, symmetric, BOUNDED information-theoretic divergence:

    M = 0.5 * D_KL(P || Avg) + 0.5 * D_KL(Q || Avg),   Avg = 0.5(P+Q)

    D_KL(P||Avg) = sum_{g in V} P(g) log2( P(g)/Avg(g) )

Properties we can legitimately claim in the paper:
  - Symmetric: JSD(P,Q) = JSD(Q,P).
  - Bounded: 0 <= JSD <= 1 bit (log2 base). 0 iff P == Q.
  - sqrt(JSD) IS a true metric (satisfies triangle inequality) — Endres &
    Schindelin (2003), Österreicher & Vajda (2003). So "distance metric" becomes
    a DEFENSIBLE claim if we report sqrt(JSD).
  - Probability-weighted: dominant n-grams matter more than rare ones, unlike
    the draft's unweighted mean.

### 2.3 Relationship back to "codelength" (keep the paper's intuition)
Cross-entropy H(P,Q) = -sum P(g) log2 Q(g) is the expected codelength of coding
text-1 n-grams with a model trained on text-2. We retain the compression framing:
  - excess codelength = H(P,Q) - H(P) = D_KL(P||Q)  (bits/n-gram wasted)
This lets the narrative keep "compression codelength" language while the metric
underneath is correct KL/JSD.

### 2.4 Per-n-gram divergence for ranking (tag clouds / top-k tables)
The draft's top-k ranking of "unusual" n-grams is genuinely useful; keep it but
correct it. Rank by pointwise contribution to JSD:

    delta(g) = 0.5*P(g)*log2(P(g)/Avg(g)) + 0.5*Q(g)*log2(Q(g)/Avg(g))

This is >= 0, sums to JSD, and identifies which n-grams drive the divergence —
a principled replacement for |log-ratio| ranking.

## 3. What "ground truth" tests must show
A quality-defect detector must map DEFECT MAGNITUDE -> METRIC RESPONSE monotonically,
and separate defective from clean corpora better than a baseline. So the harness
must produce, for each defect type and each injection rate r:
    JSD(clean, clean+defect(r))  should increase monotonically in r,
and a classifier using M must beat a token-frequency baseline at labelling
clean vs. defective (ROC-AUC, PR-AUC).

## 4. Baseline to beat
Chi-squared / raw token-frequency distance (what the draft implies is enough):
    baseline(g) = |C_T1(g)/N1 - C_T2(g)/N2|  averaged over shared vocab.
If JSD detects injected defects better than this, that's the paper's core result.
