.PHONY: test format clean preview_site
test:
	uv run pytest --cov-report xml --cov=src/manta

format:
	uv run ruff check --fix
	uv run ruff format

clean:
	git clean -Xdf

preview_site:
	uv run mike serve
