# Six-Corpus Results Memo — authoritative

**Status: full six-corpus experiment complete.** 2,400 corpus-level measurements
(5 defects x 8 rates x 6 corpora x 10 seeds) + 360 document-level runs. All
numbers below regenerate from `results_six.json` and `results_doclevel_six.json`.

## Substrate (six distinct linguistic conditions)

| Corpus | chars | tokens | types | theta |
|---|---|---|---|---|
| english (6 novels) | 4.58M | 844K | 26,660 | 0.011 |
| bible (KJV) | 4.33M | 854K | 12,744 | 0.005 |
| spanish (Don Quijote) | 2.10M | 381K | 22,960 | 0.029 |
| arabic (Qur'an) | 0.71M | 77K | 21,117 | 0.180 |
| igbo (AfriBERTa) | 2.50M | 498K | 29,591 | 0.035 |
| pidgin (AfriBERTa) | 2.50M | 447K | 18,827 | 0.022 |

theta spans 0.005-0.18, exercising the parameter-free smoothing across a wide range.

## KEY METHODOLOGICAL POINT: report WITHIN-corpus, not pooled

Pooling effect sizes across corpora is invalid here (Simpson's paradox): corpora
have different baseline r=0 divergences, so pooling inflates the SD and crushes
the effect (pooled foreign d=0.74 despite every corpus showing d=3.5-7.6). The
correct summary is the WITHIN-corpus effect size, averaged across corpora.

## Headline results (within-corpus effect size at r=0.05, RGT)

| Defect | mean d | range | class |
|---|---|---|---|
| encoding | +8.28 | [+4.55, +13.88] | content |
| foreign | +5.34 | [+3.49, +7.61] | content |
| duplicate | +0.80 | [-0.22, +1.65] | structural |
| truncate | +0.24 | [+0.10, +0.37] | structural |
| boilerplate | +0.21 | [-0.75, +0.95] | structural |

Content vs structural separation: 6.7x (smallest content effect / largest structural).

## Result 1 — encoding baseline fails in ALL SIX languages

| Corpus | RGT d | baseline d |
|---|---|---|
| english | +5.86 | -2.69 |
| bible | +6.99 | -6.51 |
| spanish | +9.54 | -9.30 |
| arabic | +4.55 | -7.41 |
| igbo | +13.88 | -1.99 |
| pidgin | +8.89 | -3.18 |

The frequency baseline has a NEGATIVE effect size at r=0.05 in every language
(-1.99 to -9.30): under light corruption it moves the WRONG WAY, reporting a
more-corrupted corpus as more similar to its clean reference. It is non-monotonic
in all six. RGT detects the defect strongly in every language. This is a
six-language regularity, far stronger than the single English demonstration in
the prior draft. (Note: the baseline does not uniformly *fall* across the whole
rate range in all six; the precise universal claim is the negative effect size
at low rate plus non-monotonicity.)

## Result 2 — foreign contamination, incl. the same-script hard case

| Corpus | r=0 -> r=0.5 | d@0.05 | note |
|---|---|---|---|
| arabic<-english | 0.006 -> 0.689 | 7.61 | different script |
| spanish<-arabic | 0.003 -> 0.141 | 7.27 | different script |
| igbo<-arabic | 0.004 -> 0.111 | 5.06 | different script |
| bible<-arabic | 0.005 -> 0.079 | 5.04 | different script |
| pidgin<-english | 0.004 -> 0.115 | 3.53 | **SAME SCRIPT, shared lexicon** |
| english<-arabic | 0.003 -> 0.074 | 3.49 | different script |

The deliberate same-script hard case (Pidgin contaminated with English: no script
change, shared lexicon) is still detected at d=3.53. The sensitivity floor is high.

## Result 3 — V&V prediction holds across all six languages

Structural defects: within-corpus corpus-level d = 0.21-0.80 (weak), but
document-level ROC-AUC = 1.000 +/- 0.000 for BOTH truncate and duplicate in EVERY
one of the six languages (36/36 per-corpus AUCs == 1.000).

Content defects: strong at corpus level (d = 5.34, 8.28), as predicted.

The verification/validation distinction predicts the right instrument in every
language tested, not just English.

## Monotonicity (RGT, fraction of 7 rate-steps increasing, mean over corpora)
foreign 1.00, encoding 1.00, duplicate 0.98, truncate 0.98, boilerplate 0.86.
(Structural defects are near-flat at corpus level, so tiny non-monotonic wobbles
appear at low rates — expected and consistent with their being document-level
defects.)

## Files
- `experiment_six.py` — six-corpus driver with foreign-contamination rotation
- `results_six.json` — corpus-level results (per corpus, per rate, 3 schemes)
- `results_doclevel_six.json` — document-level AUC (pooled + per corpus)
- `six_corpus_numbers.txt` — regenerable numeric extract
