# Contributing to ptir5

Thank you for your interest in contributing to ptir5! This document provides guidelines for contributing to the project.

## Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/photothermal/PTIR5-py.git
   cd PTIR5-py
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -e ".[dev]"
   ```

3. Run the test suite to confirm everything works:

   ```bash
   python -m pytest tests/ -v
   ```

## Code Style

- **Linting**: We use [Ruff](https://docs.astral.sh/ruff/) for linting and import sorting.
- **Type checking**: We use [mypy](https://mypy-lang.org/) in strict mode.
- **Line length**: 99 characters maximum.
- **Target Python**: 3.11+

Run both checks before submitting:

```bash
python -m ruff check src/ tests/
python -m mypy src/ptir5/
```

## Running Tests

```bash
python -m pytest tests/ -v
```

Test fixtures are real `.ptir` files located in `tests/fixtures/`. When adding tests for malformed input handling, create synthetic HDF5 files using `h5py` in pytest fixtures (see `tests/test_malformed_inputs.py` for examples).

## Pull Request Process

1. Create a feature branch from `main`:

   ```bash
   git checkout -b your-feature-name
   ```

2. Make your changes in small, logical commits.

3. Ensure all quality gates pass:

   ```bash
   python -m ruff check src/ tests/
   python -m mypy src/ptir5/
   python -m pytest tests/ -v
   ```

4. Push your branch and open a pull request against `main`.

5. Fill out the PR template with a summary of changes and test plan.

## Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `test:` — Adding or updating tests
- `ci:` — CI/CD changes
- `refactor:` — Code refactoring (no behavior change)

## Architecture Notes

- **`_reader.py`** is the only module that imports `h5py`. All other modules work with Python-native types and numpy arrays.
- The library is **read-only** — no writing to PTIR5 files.
- See `CLAUDE.md` for detailed architecture documentation.
