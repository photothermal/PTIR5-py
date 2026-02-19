# PTIR5-py Public Release Readiness Review

Review date: 2026-02-19  
Scope: `docs/index.md` plus repository-wide code, tests, docs, packaging, and CI scan.

## Executive Summary

The library has a strong core design for a read-only PTIR5 reader: clean module boundaries, typed API, fixture-backed tests, and practical docs.  
Before making the repository public, the main risks are performance behavior on large files, parser hardening for malformed inputs, and public project hygiene (CI breadth, contributor/release docs).

## Strengths

- Clear architecture and separation of concerns (`src/ptir5/_reader.py` is the only HDF5-facing module).
- Good coverage of PTIR5 measurement model classes and enums.
- Lazy-loading model is documented and consistent in normal code paths.
- Useful examples and docs structure in `docs/index.md`.
- Existing tests include regression scenarios and real fixture files.

## Findings and Recommendations

## 1) High-Impact Code Issues (P0)

1. Slice helpers currently read full datasets before slicing.
- `src/ptir5/models.py:213` (`read_spectrum`)
- `src/ptir5/models.py:217` (`read_image` on hypercubes)
- `src/ptir5/models.py:257` (`read_image` on byte stacks)
- Current behavior calls `self.data[...]`, and `self.data` reads the entire `DATA` dataset.
- Recommendation: add slice-reading methods in `HDF5Reader` and use direct dataset slicing so only requested slices are loaded.

2. Parser validation relies on `assert` in runtime paths.
- `src/ptir5/_reader.py:61`
- `src/ptir5/_reader.py:70`
- `src/ptir5/_reader.py:99`
- Recommendation: replace `assert`-based validation with explicit exceptions using `PTIR5Error` / `InvalidMeasurementError` and actionable error messages.

3. `InvalidMeasurementError` is defined but not used.
- `src/ptir5/exceptions.py:14`
- Recommendation: use it for malformed or incompatible measurement groups (missing `TYPE`, missing `DATA`, unsupported rank/dtype combinations where needed).

## 2) Correctness and Robustness (P1)

1. Unknown type fallback may misrepresent shape semantics.
- `src/ptir5/models.py:356`
- `src/ptir5/models.py:358`
- Unknown types without inferable `DATA` shape default to `FLOAT_SPECTRUM_1D`.
- Recommendation: introduce `DataShape.UNKNOWN` (or allow `None`) and document it clearly.

2. `PixelFormat` decoding only resolves enum names.
- `src/ptir5/models.py:164`
- `src/ptir5/models.py:245`
- Recommendation: support both name-based and integer-based attribute values (`PixelFormat(raw_int)` fallback).

3. Tree decoding lacks explicit malformed input handling.
- `src/ptir5/_reader.py:141`
- Recommendation: validate expected `(N,16)` shape and conversion errors; raise a typed exception with node path context.

4. Unused constant indicates minor drift.
- `_NON_ATTR_ITEMS` appears unused at `src/ptir5/_reader.py:20`.
- Recommendation: remove or implement intended usage.

## 3) Tests and QA (P1)

1. CLAUDE tooling doc appears out of sync on test count.
- `CLAUDE.md:11` says 69 tests.
- Current grep count of `def test_` indicates fewer test functions.
- Recommendation: update the doc to avoid confusion for contributors.

2. Add tests for malformed input and edge decoding:
- Missing `TYPE` attribute.
- Missing `DATA` dataset.
- Corrupt `TREE/NODES` shape/content.
- Unknown `TYPE` + missing `DATA`.
- Numeric `PixelFormat`.
- Very large dataset slice-access behavior (ensuring no full-array read in helpers).

3. Consider avoiding `sys.path` test injection for at least one CI job.
- `tests/conftest.py:10`
- Recommendation: include a wheel-install test job so packaging/import issues are caught.

## 4) CI/Release Readiness (P1)

1. CI does not match declared Python support.
- Classifiers: 3.11/3.12/3.13 in `pyproject.toml`.
- Workflow runs only 3.11 (`.github/workflows/python-app.yml:22`).
- Recommendation: use a matrix across supported versions.

2. Add packaging/release checks:
- Build sdist/wheel in CI.
- Install wheel in clean env and run smoke test.
- Optional trusted-publishing workflow for PyPI release tags.

3. Add status badges and release notes process.
- Recommendation: README badges for CI, version, license.

## 5) Documentation and Public Repo Hygiene (P1)

1. Fix invalid snippet in docs.
- `docs/tree_navigation.md:29` has `return` at top level in a script-style snippet.
- Recommendation: rewrite snippet with `if/else` flow and no top-level `return`.

2. Guard `leaf.measurement` usage in docs/examples.
- `docs/tree_navigation.md:36`
- `docs/quickstart.md:64`
- `README.md:39`
- Recommendation: check `if leaf.measurement is not None` before dereferencing.

3. Add standard public-project docs:
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CHANGELOG.md`
- `CODE_OF_CONDUCT.md`
- Issue and PR templates.

4. Clarify compatibility and scope in docs:
- PTIR Studio/PTIR5 format version compatibility policy.
- Which measurement families are covered by fixtures vs not yet validated.
- Expected memory behavior (`m.data` full read, helper slice behavior once fixed).

## 6) Feature Opportunities (P2)

1. Add a small CLI utility:
- Example: `ptir5 inspect file.ptir --json`
- Useful for quick adoption and support debugging.

2. Add selective read APIs:
- Region-of-interest reads for images/cubes.
- Multi-point spectrum extraction.
- Better support for large datasets.

3. Add optional ecosystem adapters:
- `xarray` export helper for hyperspectral workflows.

## Prioritized Next Steps

## Phase 1 (Immediate pre-public)

1. Implement reader-level dataset slicing and update helper methods to avoid full reads.
2. Replace runtime `assert` checks with explicit typed exceptions.
3. Fix docs snippet issues (`tree_navigation`, `quickstart`, README null guards).
4. Expand CI to Python 3.11/3.12/3.13 matrix.

## Phase 2 (Shortly after public launch)

1. Add malformed-input regression tests and `PixelFormat` numeric tests.
2. Add contributor/security/changelog/code-of-conduct docs and templates.
3. Add wheel smoke-test job.

## Phase 3 (Roadmap)

1. CLI inspect tool.
2. Additional selective read APIs and performance-oriented helpers.
3. Optional interoperability helpers (`xarray`).

## Validation Note

In this review environment, dependency installation and online package fetch were unavailable, so full `pytest` / `ruff` / `mypy` execution could not be completed here. Recommendations above are based on static code and doc inspection plus repository structure analysis.
