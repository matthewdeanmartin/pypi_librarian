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

check: lint typecheck test build

# ── Python 3.15 trial run ─────────────────────────────────────────────────────
# Uses a dedicated venv so the normal .venv is never touched.

PY315 := 3.15.0rc2
VENV315 := .venv315rc2
PY315_EXE := $(VENV315)/Scripts/python.exe

.PHONY: venv315
venv315:
	@echo "Creating Python $(PY315) trial venv at $(VENV315)"
	@test -x $(PY315_EXE) || $(UV) venv $(VENV315) --python $(PY315)
	$(UV) pip install -e . pytest pytest-cov pytest-timeout pytest-mock pytest-asyncio pytest-httpx --python $(PY315_EXE)

.PHONY: venv315-clean
venv315-clean:
	@echo "Recreating Python $(PY315) trial venv from scratch"
	$(UV) venv $(VENV315) --python $(PY315) --clear
	@$(MAKE) venv315

.PHONY: test315
test315: venv315
	@echo "Running unit tests on Python $(PY315)"
	$(PY315_EXE) -m pytest $(TESTS) -q --timeout=60 -p no:randomly -p no:sugar

.PHONY: check315
check315: test315
	@echo "Python $(PY315) checks passed."

build: clean
	$(UV) build
	$(UV) run twine check dist/*

publish-check: build

clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for path in ['build', 'dist', 'pypi_librarian.egg-info', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov'] if Path(path).exists()]"


# ── Dogfooding targets (independent, not wired into check) ───────────────────

.PHONY: version-check
version-check:
	@$(UV) jiggle_version check

.PHONY: dev-status
dev-status:
	@$(UV) troml-dev-status validate .

.PHONY: prerelease-check
prerelease-check: version-check dev-status
	@echo "Pre-release checks passed."

.PHONY: dont-be-lazy
dont-be-lazy:
	@$(UV) dont_be_lazy --root . --no-color summary
	@$(UV) dont_be_lazy --root . --no-color scan pypi_librarian --no-config-suppressions || true

.PHONY: pydoc-docs
pydoc-docs:
	@$(UV) pydoc_fork pypi_librarian -o ./pydoc/
