.PHONY: install run test gen check-generated

install:
	pip install -e ".[dev]"

run:
	SHIPCALC_API_KEY=dev-placeholder uvicorn shipcalc.main:app --reload --port 8080

test:
	SHIPCALC_API_KEY=test-placeholder pytest -q

gen:
	python scripts/gen_rates.py data/rates.csv src/shipcalc/generated/rates_table.py

check-generated: gen
	git diff --exit-code src/shipcalc/generated/
