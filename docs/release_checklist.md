# PTIR5-py Release Checklist

Checklist of tasks to complete before making the repository public.

## Critical (Do Before Public Release)

- [ ] Implement reader-level dataset slicing to avoid full-array loads in helper methods.
- [ ] Update `FloatHypercube3D.read_spectrum` to use slice reads instead of `self.data`.
- [ ] Update `FloatHypercube3D.read_image` to use slice reads instead of `self.data`.
- [ ] Update `ByteImageStack3D.read_image` to use slice reads instead of `self.data`.
- [ ] Replace runtime `assert` checks in reader code with explicit typed exceptions.
- [ ] Use `InvalidMeasurementError` for malformed/invalid measurement structures.
- [ ] Add explicit validation and errors for malformed `TREE/NODES` datasets.
- [ ] Fix invalid top-level `return` in `docs/tree_navigation.md` example.
- [ ] Add `leaf.measurement is not None` guards in tree snippets in `README.md` and docs.
- [ ] Expand CI workflow to test Python 3.11, 3.12, and 3.13.

## High Priority (Should Do Before or Immediately After Release)

- [ ] Add tests for missing `TYPE` attribute.
- [ ] Add tests for missing `DATA` dataset.
- [ ] Add tests for corrupted `TREE/NODES` shape/content.
- [ ] Add tests for unknown `TYPE` with missing/nonstandard datasets.
- [ ] Add tests for numeric `PixelFormat` values (not just enum names).
- [ ] Decide and implement behavior for unknown data shape (`DataShape.UNKNOWN` or equivalent).
- [ ] Improve unknown-type fallback so shape semantics are not misrepresented.
- [ ] Remove or implement currently unused `_NON_ATTR_ITEMS` constant.
- [ ] Update `CLAUDE.md` test count/tooling notes to match current repository state.
- [ ] Add a CI job that builds wheel/sdist and runs an install smoke test from built artifacts.

## Public Repository Hygiene

- [ ] Add `CONTRIBUTING.md`.
- [ ] Add `SECURITY.md` with vulnerability reporting instructions.
- [ ] Add `CHANGELOG.md` with release process/versioning notes.
- [ ] Add `CODE_OF_CONDUCT.md`.
- [ ] Add issue templates and pull request template.
- [ ] Add README badges (CI status, version, license).
- [ ] Document compatibility policy (PTIR Studio/PTIR5 versions supported).
- [ ] Document memory/performance behavior clearly (`m.data` full read vs slice helpers).

## Nice-to-Have (Post-Release Roadmap)

- [ ] Add a CLI tool (e.g., `ptir5 inspect <file> --json`).
- [ ] Add selective read APIs for ROI/region-based access.
- [ ] Add helpers for multi-point extraction from hyperspectral data.
- [ ] Add optional interoperability helper(s), such as `xarray` export.
