.PHONY: test format clean serve_docs
test:
	pytest

format:
	black .

clean:
	git clean -Xdf

serve_docs:
	mkdocs serve
