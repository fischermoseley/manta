.PHONY: build test format clean preview_site pre-commit

build:
	uv build

test:
	uv run pytest --cov-report xml --cov-report markdown --cov=src/manta

format:
	uv run ruff check --fix
	uv run ruff format

clean:
	git clean -Xdf

preview_site:
	uv run mike serve

pre-commit:
	uv run pre-commit run --all-files
