.PHONY: test format clean serve_docs
test:
	python3 -m pytest

format:
	python3 -m black .

clean:
	git clean -Xdf

preview_site:
	mkdocs serve
