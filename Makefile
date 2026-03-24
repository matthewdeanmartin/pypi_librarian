UV ?= uv
PYTHON ?= python
PACKAGE := pypi_librarian
TESTS := test

.PHONY: help sync format format-check lint typecheck test check build publish-check clean

help:
	@echo Available targets: sync format format-check lint typecheck test check build publish-check clean

sync:
	$(UV) sync --group dev

format:
	$(UV) run black $(PACKAGE) $(TESTS)
	$(UV) run ruff check --fix $(PACKAGE) $(TESTS)

format-check:
	$(UV) run black --check $(PACKAGE) $(TESTS)
	$(UV) run ruff check $(PACKAGE) $(TESTS)

lint:
	$(UV) run ruff check $(PACKAGE) $(TESTS)
	$(UV) run bandit -q -r $(PACKAGE)
	$(UV) run vulture $(PACKAGE) $(TESTS)
	$(UV) run python -m compileall $(PACKAGE)

typecheck:
	$(UV) run mypy --no-namespace-packages $(PACKAGE)

test:
	$(UV) run pytest -q

check: format-check lint typecheck test build

build: clean
	$(UV) build
	$(UV) run twine check dist/*

publish-check: build

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in ['build', 'dist', 'pypi_librarian.egg-info', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov'] if Path(path).exists()]"

