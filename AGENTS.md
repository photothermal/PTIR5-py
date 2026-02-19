# Repository Guidelines

## Project Structure & Module Organization

- `src/ptir5/`: package source code.
- `src/ptir5/file.py`: high-level file API (`PTIR5File`).
- `src/ptir5/_reader.py`: low-level HDF5 access (the only module that imports `h5py`).
- `src/ptir5/models.py`: typed measurement classes and dispatch.
- `src/ptir5/tree.py`, `src/ptir5/metadata.py`, `src/ptir5/enums.py`: tree navigation, metadata mapping, enums.
- `tests/`: `pytest` suite and regression tests.
- `tests/fixtures/`: sample `.ptir` files used by tests.
- `docs/`: user and developer documentation.
- `examples/`: runnable usage scripts.

## Build, Test, and Development Commands

- `pip install -e ".[dev]"`: install package + dev tools in editable mode.
- `python -m pytest tests/ -v`: run the full test suite.
- `python -m ruff check src/ tests/`: lint and import-order checks.
- `python -m mypy src/ptir5/`: strict type checking.
- `python -m pytest -q`: quick local test run.

Run all three quality gates (`pytest`, `ruff`, `mypy`) before opening a PR.

## Coding Style & Naming Conventions

- Python 3.11+ codebase, 4-space indentation, type hints required.
- Ruff line length: 99 (`pyproject.toml`).
- Keep modules focused; avoid adding `h5py` imports outside `_reader.py`.
- Use descriptive `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Preserve lazy-loading behavior for data/metadata access paths.

## Testing Guidelines

- Framework: `pytest` with tests under `tests/test_*.py`.
- Add regression tests for every bug fix (see `tests/test_regressions.py`).
- Prefer fixture-based tests using files in `tests/fixtures/`.
- For parser/edge-case changes, include malformed/minimal-file tests where possible.

## Commit & Pull Request Guidelines

- Recent history uses short imperative summaries, sometimes with prefixes (for example: `ci: ...`, `Fix ...`, `Add ...`).
- Keep commits focused and atomic; separate refactors from behavior changes.
- PRs should include:
- A clear summary and motivation.
- Linked issue(s) if applicable.
- Test evidence (commands run and results).
- Docs updates when public API or behavior changes.

## Security & Configuration Notes

- Do not commit proprietary PTIR data; only sanitized fixtures belong in `tests/fixtures/`.
- Treat malformed `.ptir` inputs as untrusted; prefer explicit exceptions over silent fallback behavior.
