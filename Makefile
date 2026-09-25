UV_ANALYSIS = uv run --with 'numpy>=1.26' --with 'scipy>=1.11'

.PHONY: check analysis sweep data clean-ids run

# Reproduce every write-up figure from the committed results; needs no API key or dataset
check:
	$(UV_ANALYSIS) --with pytest pytest -q

analysis:
	$(UV_ANALYSIS) analyze.py > results/analysis.txt

sweep:
	$(UV_ANALYSIS) threshold_sweep.py > results/threshold_sweep.txt

data:
	python3 fetch_data.py

clean-ids: data
	python3 lexical.py

# Spends real Jev credit (about US$0.51 for the full run); needs TYPESAFE_API_KEY
run: data
	uv run run.py
