# V & V Pipeline Usage Guide

This project is an experimental pipeline for testing corpus-quality
metrics using controlled defect injection.

## What the pipeline does

The code compares a clean reference corpus against a test corpus after a known
defect has been injected. It supports two levels of analysis:

- Corpus-level evaluation with information-theoretic divergence metrics.
- Document-level evaluation for structural defects such as duplication and
  truncation.

The main scripts are:

- `experiment.py` - runs the main dose-response experiment and writes
  `results_both.json`.
- `doclevel.py` - runs document-level detection experiments and writes
  `results_doclevel.json`.
- `defects.py` - defect injection helpers and document splitting utilities.
- `metric.py` - tokenization and divergence metric functions.
- `rgt.py` - reciprocal Good-Turing variant used by `experiment.py`.

## Requirements

- Python 3.10 or newer.
- `numpy`.

The scripts otherwise use the Python standard library.

## Expected data layout

Run the code from this folder so the relative paths work correctly.

The scripts expect a `corpora/` directory containing plain-text files such as:

- `corpora/pride_prejudice.txt`
- `corpora/sherlock.txt`
- `corpora/tale_two_cities.txt`
- `corpora/great_expect.txt`
- `corpora/dubliners.txt`
- `corpora/moby_dick.txt`
- `corpora/arabic_quran.txt`

If those files are missing, the runners will fail when they try to load the
corpora.

## Setup

Create and activate a virtual environment, then install the dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the experiments

### 1. Main corpus-level experiment

Run all defects:

```bash
python experiment.py
```

Run only selected defects:

```bash
python experiment.py duplicate foreign
```

This creates or updates `results_both.json` in the project directory.

### 2. Document-level experiment

```bash
python doclevel.py
```

This writes `results_doclevel.json`.

### 3. Metric sanity check

```bash
python metric.py
```

This prints a quick check showing that identical texts score near zero and
clearly different texts score higher.

## Output files

- `results_both.json` stores the corpus-level results for each defect and
  injection rate.
- `results_doclevel.json` stores the document-level ROC-AUC summaries.

## Notes

- Run everything from the repository root so the relative `corpora/...` paths
  resolve correctly.
- The pipeline uses random seeds, so results are reproducible across runs as
  long as the code and corpus files stay the same.
