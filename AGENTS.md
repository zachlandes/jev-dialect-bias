# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- `make check` must pass before any change goes in: it recomputes every figure in `docs/WRITEUP.md`, `results/analysis.txt` and `prompts.json` from the committed results (tests in `tests/test_reproduce.py`).
  After changing `analyze.py` output, run `make analysis`; after changing prompts in `run.py`, run `python3 run.py --dump-prompts`.
- Never commit or quote the Groenwold tweet texts (research-use terms): `data/` is gitignored, results hold probabilities only, and analysis prints aggregates only.
  The three clean example pairs in `docs/WRITEUP.md` and `docs/writeup.html` are the only deliberate exception.
- `results/results.jsonl` is the published run's raw record; never rewrite or reformat it.
  The three-way tie rule in `analyze.py` depends on its option order.
- `docs/writeup.html` is the published page as-is; `docs/WRITEUP.md` is its Markdown conversion, and the two must say the same thing.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
