# Supplemental Material
## Operationalizing Verification and Validation for Text Corpora: A Parameter-Free Information-Theoretic Framework

This package contains the LaTeX source to compile the paper and a **single
self-contained Jupyter notebook** that reproduces the entire experiment.

## Contents

### Paper source 
- `main.tex`        — paper source (IEEEtran conference class)
- `refs.bib`        — bibliography
- `fig_smoothing_six.pdf`      — Fig. 1 (add-k vs RGT effect size)
- `fig_dose_sixcorpus.pdf`     — Fig. 2 (dose-response by defect class)
- `fig_encoding_sixcorpus.pdf` — Fig. 3 (encoding: RGT vs baseline, six languages)
- `fig_foreign_sixcorpus.pdf`  — Fig. 4 (foreign contamination per corpus)
- `paper_main.pdf`        — compiled paper

### Experiment (single notebook)
- `corpus_vv_experiment.ipynb`  — the complete pipeline, end to end:
  metric + RGT smoothing, corpus acquisition, defect injection, the six-corpus
  corpus-level experiment, document-level detection, analysis, and all figures.
  Markdown narrative follows the paper's logical chain
  (problem -> evidence-location principle -> defect->level -> RGT -> ground truth
  -> experiment -> results). All randomness is seeded.

- `corpus_vv_executed.ipynb`    — the same notebook, pre-run with outputs and
  figures rendered, so results can be read without executing anything.

### Cached results (let the notebook load instantly; also regenerate the paper's tables)
- `results_six.json`          — corpus-level: per corpus x rate x {rgt, addk, baseline}
- `results_doclevel_six.json` — document-level ROC-AUC
- `smoothing_sweep_six.json`  — add-k vs RGT effect size across k
- `six_corpus_numbers.txt`    — human-readable numeric summary
- `RESULTS_MEMO_CORPUS.md`       — annotated results walkthrough

## Reproducing from scratch

1. Open `corpus_vv_experiment.ipynb` in Jupyter (Python 3; needs numpy, scipy,
   regex, matplotlib — the first cell installs any that are missing).
2. Run the cells top to bottom. The corpus-acquisition cell (Step 5) fetches the
   four public corpora automatically; place the two AfriBERTa corpora manually
   first (see the data note below).
3. The experiment cell caches to `results_six.json`; if that file is present it
   loads instantly instead of re-running the ~15-minute sweep.
4. Figures render inline in the results section.

## Data note

The corpora are public or openly licensed, but we ship acquisition code (inside
the notebook) rather than the text itself:
- english, bible, spanish: Project Gutenberg (public domain) — fetched automatically.
- arabic: Qur'an text (risan/quran-json) — fetched automatically.
- igbo, pidgin: AfriBERTa corpus (Ogueji et al., 2021), predominantly BBC News.
  Obtain from the AfriBERTa dataset and place as corpora/igbo.txt and
  corpora/pidgin.txt (trim to ~2.5M chars, drop lines < 20 chars). Not redistributed.

The notebook prints exactly which corpora are present and which are still needed.

## Key numbers 

- 2,400 corpus-level + 360 document-level measurements
  (corpus-level: 5 defects x 8 rates x 6 corpora x 10 seeds;
   document-level: 2 defects x 3 rates x 6 corpora x 10 seeds).
- Content-defect within-corpus effect size at r=0.05: encoding d=8.28, foreign d=5.34.
- Frequency baseline effect size on encoding is negative in all six languages
  (-1.99 to -9.30): it moves the wrong way under light corruption.
- Structural defects: corpus-level d<=0.8, document-level ROC-AUC = 1.000.
