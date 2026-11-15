.PHONY: test format clean serve_docs
test:
	python3 -m pytest --cov-report xml --cov=src/manta

format:
	python3 -m ruff check --extend-select I --ignore SIM117 --fix
	python3 -m ruff format

clean:
	git clean -Xdf

preview_site:
	mike serve
