.PHONY: test format clean serve_docs
test:
	python3 -m pytest --cov-report xml --cov=src/manta test/

format:
	python3 -m ruff check --select I --fix
	python3 -m ruff format

clean:
	git clean -Xdf

preview_site:
	mike serve
