"""
Defect-injection harness — the ground truth for corpus-quality detection.

Principle: start from a CLEAN corpus, inject a KNOWN defect at a KNOWN rate,
so the correct answer is controlled. A quality metric that works must respond
monotonically to injection rate and separate clean from defective corpora.

Each injector takes a list of "documents" (strings) + a rate r in [0,1] and a
RNG, and returns a NEW list of documents with the defect applied. Injectors are
deterministic given the seed.

Defect types (drawn from the source paper's own V&V task list):
  duplicate      : replace a fraction of docs with copies of other docs
  foreign        : replace a fraction of docs with foreign-language text
  truncate       : cut a fraction of docs down to a few tokens (short/empty docs)
  encoding       : corrupt a fraction of characters (mojibake / bad transliteration)
  shuffle_align  : (parallel) permute a fraction of target docs -> misalignment
  boilerplate    : inject repeated boilerplate lines into a fraction of docs
"""
from __future__ import annotations
import random
import re
from typing import Callable


def _pick_indices(n: int, rate: float, rng: random.Random) -> set:
    k = round(n * rate)
    if k <= 0:
        return set()
    return set(rng.sample(range(n), min(k, n)))


def inject_duplicate(docs, rate, rng, **kw):
    """Replace `rate` fraction of docs with exact copies of randomly chosen other docs."""
    docs = list(docs)
    idx = _pick_indices(len(docs), rate, rng)
    for i in idx:
        src = rng.randrange(len(docs))
        docs[i] = docs[src]
    return docs


def inject_foreign(docs, rate, rng, foreign_pool=None, **kw):
    """Replace `rate` fraction of docs with foreign-language documents."""
    if not foreign_pool:
        raise ValueError("foreign injection needs a foreign_pool of docs")
    docs = list(docs)
    idx = _pick_indices(len(docs), rate, rng)
    for i in idx:
        docs[i] = rng.choice(foreign_pool)
    return docs


def inject_truncate(docs, rate, rng, keep_tokens=5, **kw):
    """Truncate `rate` fraction of docs to the first `keep_tokens` tokens (short/empty)."""
    docs = list(docs)
    idx = _pick_indices(len(docs), rate, rng)
    for i in idx:
        toks = docs[i].split()
        docs[i] = " ".join(toks[:keep_tokens])
    return docs


def inject_encoding(docs, rate, rng, char_rate=0.15, **kw):
    """Corrupt `char_rate` of characters in `rate` fraction of docs (mojibake)."""
    docs = list(docs)
    idx = _pick_indices(len(docs), rate, rng)
    subs = "�Ã¢â‚¬Å½ÐÑ"  # mojibake-ish replacement chars
    for i in idx:
        chars = list(docs[i])
        for j in range(len(chars)):
            if chars[j].strip() and rng.random() < char_rate:
                chars[j] = rng.choice(subs)
        docs[i] = "".join(chars)
    return docs


def inject_boilerplate(docs, rate, rng, boiler=None, repeats=8, **kw):
    """Inject repeated boilerplate into `rate` fraction of docs (the aljazeera.txt case)."""
    if boiler is None:
        boiler = "click here to subscribe to our newsletter for the latest updates"
    docs = list(docs)
    idx = _pick_indices(len(docs), rate, rng)
    for i in idx:
        docs[i] = docs[i] + (" " + boiler) * repeats
    return docs


def permute_fraction(target_docs, rate, rng, **kw):
    """
    Parallel-corpus misalignment: permute `rate` fraction of target docs so they
    no longer line up with their source. Returns permuted target list.
    (Alignment metrics operate on aligned PAIRS; this breaks a known fraction.)
    """
    target = list(target_docs)
    idx = sorted(_pick_indices(len(target), rate, rng))
    if len(idx) >= 2:
        vals = [target[i] for i in idx]
        # derange the selected subset
        rng.shuffle(vals)
        for i, v in zip(idx, vals):
            target[i] = v
    return target, set(idx)


INJECTORS: dict[str, Callable] = {
    "duplicate": inject_duplicate,
    "foreign": inject_foreign,
    "truncate": inject_truncate,
    "encoding": inject_encoding,
    "boilerplate": inject_boilerplate,
}


# ---- document splitting utilities -------------------------------------------

def to_documents(text: str, target_docs: int = 200) -> list[str]:
    """
    Split a raw text into ~target_docs pseudo-documents of roughly equal size.

    Splits on blank lines (paragraphs); if a text has too few blank-line breaks
    (e.g. verse-per-line files), falls back to single newlines, then to sentence
    boundaries. Finally regroups units into `target_docs` buckets so that
    documents from DIFFERENT corpora are comparable in size — essential when
    documents are swapped between corpora (foreign-contamination injection).
    """
    units = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    # Fallback 1: no blank-line structure -> split on single newlines
    if len(units) < target_docs:
        units = [p.strip() for p in text.split("\n") if p.strip()]
    # Fallback 2: still too few -> split on sentence enders
    if len(units) < target_docs:
        units = [s.strip() for s in re.split(r"(?<=[.!?\u061F\u06D4])\s+", text) if s.strip()]
    if not units:
        return []

    # Regroup units into exactly ~target_docs buckets
    if len(units) <= target_docs:
        return units
    per = len(units) / target_docs
    chunks, buf, acc = [], [], 0.0
    for u in units:
        buf.append(u)
        acc += 1
        if acc >= per:
            chunks.append(" ".join(buf))
            buf, acc = [], 0.0
    if buf:
        chunks.append(" ".join(buf))
    return [c for c in chunks if c.strip()]


if __name__ == "__main__":
    txt = open("corpora/pride_prejudice.txt", encoding="utf-8").read()
    docs = to_documents(txt, 200)
    print(f"pride_prejudice -> {len(docs)} docs, "
          f"median tokens={sorted(len(d.split()) for d in docs)[len(docs)//2]}")
    rng = random.Random(1)
    d2 = inject_duplicate(docs, 0.2, rng)
    dupes = sum(1 for i in range(len(d2)) if d2.count(d2[i]) > 1)
    print(f"after 20% duplicate injection: {dupes} docs are now non-unique")
