"""Check that the committed results reproduce every figure in the write-up.

Run with `make check`. Tests that need the Groenwold texts skip unless data/ exists
(python3 fetch_data.py).
"""
import contextlib
import io
import json
import os
import re

import pytest

import analyze
import run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "results.jsonl")
WRITEUP = open(os.path.join(ROOT, "docs", "WRITEUP.md"), encoding="utf-8").read()
README = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
HAS_DATA = os.path.exists(os.path.join(ROOT, "data", "aave_samples.txt"))
# Pair ids of the three clean examples quoted in the write-up
EXAMPLES = (81, 70, 21)


@pytest.fixture(scope="module")
def R():
    os.chdir(ROOT)
    return analyze.load(RESULTS)[0]


@pytest.fixture(scope="module")
def clean():
    return analyze.load_clean(os.path.join(ROOT, "clean_ids.txt"))


def pts(x):
    """Percentage points to one decimal, typeset as in the write-up."""
    return f"{x * 100:+.1f}".replace("-", "−")


def pct(x):
    return f"{x * 100:.1f}%"


def ci(s):
    return f"{pts(s['diff'])} pts [{pts(s['lo'])}, {pts(s['hi'])}]"


def in_writeup(s):
    assert s in WRITEUP, f"{s!r} not in docs/WRITEUP.md"


def in_readme(s):
    assert s in README, f"{s!r} not in README.md"


def test_results_hold_no_text():
    key_rx = re.compile(r"^[abc]\|neutral$|^[abc]\|\d+\|(aae|sae)$|^d\|\d+\|sae_(black|white)$|^a\|\d+\|(aae|sae)\|replay$")
    options = {"acquitted", "convicted", "life", "death", "allow", "remove", "needs_human_review"}
    for line in open(RESULTS):
        r = json.loads(line)
        assert set(r) == {"key", "model", "tokens", "p"}
        assert key_rx.match(r["key"]), r["key"]
        assert r["model"] == run.MODEL and isinstance(r["tokens"], int)
        for q, dist in r["p"].items():
            assert re.fullmatch(r"guilt[012]|penalty[012]|mod[23]", q)
            assert set(dist) <= options and all(isinstance(v, (int, float)) for v in dist.values())


def test_grid_is_complete(R):
    assert set(R) == analyze.expected_keys()


def test_prompts_json_matches_runner():
    with open(os.path.join(ROOT, "prompts.json")) as f:
        assert json.load(f) == {v: run.questions(v) for v in run.VARIANTS}


def test_committed_analysis_is_current():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        analyze.report(RESULTS)
    with open(os.path.join(ROOT, "results", "analysis.txt")) as f:
        assert buf.getvalue() == f.read(), "rerun: uv run analyze.py > results/analysis.txt"


def test_run_summary():
    _, tokens, models = analyze.load(RESULTS)
    assert models == {"jev-1.13.0"}
    in_writeup(f"US${tokens * analyze.PRICE_PER_TOKEN:.2f}")
    in_writeup(f"{len(analyze.expected_keys()):,} requests")


def test_judge_decisions(R):
    ids = range(analyze.N_PAIRS)
    conv = analyze.contrast(R, "a", "convicted", "aae", "sae", ids, "dec")
    death = analyze.contrast(R, "a", "death", "aae", "sae", ids, "dec")
    note = analyze.contrast(R, "b", "death", "aae", "sae", ids, "dec")
    in_writeup(f"| Convicted | {pct(conv['x'])} | {pct(conv['y'])} | {ci(conv)} |")
    in_writeup(f"| Sentenced to death | {pct(death['x'])} | {pct(death['y'])} | {ci(death)} |")
    in_writeup(f"penalised | | {ci(note)} |")


def test_moderation(R, clean):
    full = range(analyze.N_PAIRS)
    rows = {v: analyze.contrast(R, v, "remove2", "aae", "sae", full, "prob") for v in "abc"}
    plain_clean = analyze.contrast(R, "a", "remove2", "aae", "sae", clean, "prob")
    in_writeup(f"| Plain | {ci(rows['a'])} | {ci(plain_clean)} |")
    in_writeup(f"| \"Dialect is not evidence\" | {ci(rows['b'])} |")
    in_writeup(f"| Written moderation policy | {ci(rows['c'])} |")
    # "smaller, not significant" on the clean subset for both instructions
    for v in "bc":
        s = analyze.contrast(R, v, "remove2", "aae", "sae", clean, "prob")
        assert s["lo"] < 0 < s["hi"] and s["diff"] < plain_clean["diff"]

    dec = analyze.contrast(R, "a", "remove2", "aae", "sae", full, "dec")
    in_writeup(f"**{pct(dec['x'])} vs {pct(dec['y'])}** | Posts removed by the moderator")
    in_writeup(f"(about {round((dec['x'] / dec['y'] - 1) * 100)}% more removals)")
    dec_clean = analyze.contrast(R, "a", "remove2", "aae", "sae", clean, "dec")
    in_writeup(f"**{pct(dec_clean['x'])} vs {pct(dec_clean['y'])}** | Posts removed on the clean subset")

    # Instructions "roughly halved" the gap and none closed it
    assert all(rows[v]["lo"] > 0 for v in "abc")
    assert 0.4 < rows["b"]["diff"] / rows["a"]["diff"] < 0.65
    assert 0.4 < rows["c"]["diff"] / rows["a"]["diff"] < 0.65

    share, n_dirty, _, _ = analyze.gap_share(R, clean)
    in_writeup(f"{round(share * 100)}% of the full-dataset gap comes from the {n_dirty} pairs")
    in_writeup(f"clean subset** of {len(clean):,} pairs, dropping the {n_dirty} pairs")


def test_referrals(R, clean):
    s = analyze.contrast(R, "a", "review3", "aae", "sae", clean, "dec")
    in_writeup(f"{s['nx']} AAE vs {s['ny']} SAE with plain instructions, within noise")
    assert s["lo"] < 0 < s["hi"]
    # Probability of review is higher for AAE even though referrals are not
    assert analyze.contrast(R, "a", "review3", "aae", "sae", clean, "prob")["diff"] > 0


def test_overt_probe(R):
    ids = range(analyze.N_PAIRS)
    c = lambda m, k: analyze.contrast(R, "d", m, "sae_black", "sae_white", ids, k)
    death = c("death", "dec")
    rate = f"{pct(death['x'])} vs {pct(death['y'])}"
    in_writeup(f"**{rate}** | Death-sentence rate when told the writer is Black vs White")
    in_writeup(f"| Sentenced to death (decision rate) | {rate} |")
    in_writeup(f"| Convicted (probability) | {pts(c('convicted', 'prob')['diff'])} pts |")
    in_writeup(f"| Sentenced to death (probability) | {pts(c('death', 'prob')['diff'])} pts |")
    in_writeup(f"| Post removed (probability) | {pts(c('remove2', 'prob')['diff'])} pts |")


def test_example_scores(R):
    def line(p):
        return (f"`P(death) {analyze.prob(p, 'death'):.2f} · P(convicted) {analyze.prob(p, 'convicted'):.2f} "
                f"· P(remove) {analyze.prob(p, 'remove2'):.2f}`")
    for i in EXAMPLES:
        in_writeup(f"| {line(R[f'a|{i}|aae'])} | {line(R[f'a|{i}|sae'])} |")
    penalty0 = R["a|81|aae"]["penalty0"]
    in_writeup(f'{{ "life": {penalty0["life"]}, "death": {penalty0["death"]} }}')


def test_readme_tables(R, clean):
    full = range(analyze.N_PAIRS)
    bare = lambda s: f"{pts(s['diff'])} [{pts(s['lo'])}, {pts(s['hi'])}]"
    rows = [("Convicted", "a", "convicted"), ("Sentenced to death", "a", "death"),
            ("Sentenced to death, with the dialect line", "b", "death")]
    for label, v, m in rows:
        s = analyze.contrast(R, v, m, "aae", "sae", full, "dec")
        in_readme(f"| {label} | {pct(s['x'])} | {pct(s['y'])} | {bare(s)} |")
    for label, v in (("Plain", "a"), ("Dialect line", "b"), ("Written policy", "c")):
        f = analyze.contrast(R, v, "remove2", "aae", "sae", full, "prob")
        c = analyze.contrast(R, v, "remove2", "aae", "sae", clean, "prob")
        in_readme(f"| {label} | {bare(f)} | {bare(c)} |")
    d = lambda m, k: analyze.contrast(R, "d", m, "sae_black", "sae_white", full, k)
    in_readme(f"| Convicted, probability | {pts(d('convicted', 'prob')['diff'])} |")
    in_readme(f"| Sentenced to death, probability | {pts(d('death', 'prob')['diff'])} |")
    death = d("death", "dec")
    in_readme(f"| Sentenced to death, decision rate | {pct(death['x'])} vs {pct(death['y'])} |")
    in_readme(f"| Removed, probability | {pts(d('remove2', 'prob')['diff'])} |")
    share = analyze.gap_share(R, clean)[0]
    in_readme(f"{share * 100:.1f}% of the summed full-dataset gap")
    ref = analyze.contrast(R, "a", "review3", "aae", "sae", clean, "dec")
    in_readme(f"{ref['nx']} AAE vs {ref['ny']} SAE posts, within noise")


@pytest.mark.skipif(not HAS_DATA, reason="needs data/ from fetch_data.py")
def test_clean_ids_and_nword_counts(clean):
    import lexical
    os.chdir(ROOT)
    aae, sae = run.load_pairs()
    assert lexical.clean_ids(aae, sae) == clean
    n_aae = sum(bool(lexical.NWORD.search(t)) for t in aae)
    n_sae = sum(bool(lexical.NWORD.search(t)) for t in sae)
    in_writeup(f"{n_aae} AAE posts contain the n-word against {n_sae} of their translations")
    assert len(aae) * 2 == 4038 and "4,038 statements" in WRITEUP
    for i in EXAMPLES:
        # The write-up quotes the AAE side verbatim
        in_writeup(aae[i])
