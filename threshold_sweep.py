# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy>=1.26", "scipy>=1.11"]
# ///
"""Can one shared removal cutoff close the AAE/SAE moderation gap?

Usage: uv run threshold_sweep.py [results/results.jsonl] > results/threshold_sweep.txt

Uses only the saved two-way P(remove) answers; no Jev calls. A post is removed when
P(remove) > cutoff, the same rule as analyze.py's 0.5 decision. Jev reports two
decimals, so "> 0.30" means "at least 0.31" and the cutoffs sit on a 0.01 grid.
"""
import sys

import numpy as np

import analyze

CUTOFFS = [round(0.30 + 0.05 * k, 2) for k in range(13)]
BANDS = [(0.3, 0.7), (0.4, 0.8)]


def scores(R, v, ids):
    aae = np.array([R[f"{v}|{i}|aae"]["mod2"]["remove"] for i in ids])
    sae = np.array([R[f"{v}|{i}|sae"]["mod2"]["remove"] for i in ids])
    return aae, sae


def rates(x, y):
    """Mean of two per-pair 0/1 arrays, with the pair-bootstrap interval of the gap."""
    lo, hi = analyze.boot_ci(x - y)
    return dict(x=x.mean(), y=y.mean(), diff=(x - y).mean(), lo=lo, hi=hi,
                ratio=x.mean() / y.mean() if y.mean() else float("nan"))


def sweep(R, v, ids):
    aae, sae = scores(R, v, ids)
    return {t: rates((aae > t).astype(float), (sae > t).astype(float)) for t in CUTOFFS}


def bands(R, v, ids, low, high):
    aae, sae = scores(R, v, ids)
    review = rates(((aae > low) & (aae <= high)).astype(float), ((sae > low) & (sae <= high)).astype(float))
    remove = rates((aae > high).astype(float), (sae > high).astype(float))
    return review, remove


def line(s):
    return (f"AAE={s['x'] * 100:5.1f}% SAE={s['y'] * 100:5.1f}% "
            f"gap={analyze.pp(s['diff'])} [{analyze.pp(s['lo'])}, {analyze.pp(s['hi'])}] ratio={s['ratio']:.2f}")


def report(path):
    R = analyze.load(path)[0]
    subsets = (("FULL", list(range(analyze.N_PAIRS))), ("CLEAN", analyze.load_clean()))
    print("=== Shared cutoff sweep, two-way question: removed when P(remove) > cutoff ===")
    print("gap = AAE - SAE removal rate (pp), 95% pair bootstrap; ratio = AAE / SAE")
    for sub, ids in subsets:
        for v in "abc":
            print(f"\n-- {sub} {v} ({analyze.VARIANT_NAMES[v]}) --")
            for t, s in sweep(R, v, ids).items():
                print(f"> {t:.2f}  " + line(s))

    print("\n=== Three bands: remove above high, human review between, keep at or below low ===")
    for sub, ids in subsets:
        for v in "abc":
            print(f"\n-- {sub} {v} ({analyze.VARIANT_NAMES[v]}) --")
            for low, high in BANDS:
                review, remove = bands(R, v, ids, low, high)
                print(f"{low:.1f}-{high:.1f} review  " + line(review))
                print(f"{low:.1f}-{high:.1f} remove  " + line(remove))


if __name__ == "__main__":
    report(sys.argv[1] if len(sys.argv) > 1 else "results/results.jsonl")
