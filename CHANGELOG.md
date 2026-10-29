# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `TimeDomainBurst` and `TimeDomainCube` measurement types (PSC.PTIR5.SDK time-domain capture); previously these loaded as generic `Measurement`
- `HyperspectralCube` base class for `OPTIRHyperspectra`, `RamanHyperspectra` and `TimeDomainCube`
- `FLPTIRImage.data_float32` and `FLPTIRImage.is_legacy` properties
- `Measurement.auxiliary` (`AuxiliaryDatasets`) for the per-pixel and per-frame side datasets stored next to `DATA`, including `BackgroundScale`, `PumpWavelength` and `StokesWavelength`
- `component_completion` on cubes and image stacks, decoding the opt-in `ComponentCompletion` marker (`None` only when the marker is absent; any value other than 1 reads as incomplete; a marker that is not a `uint8` dataset of the expected shape raises `InvalidMeasurementError`)
- Normalization settings: `NormalizeMode`, `NormalizeSpec`, `HyperspectralCube.normalize_spec` / `supported_normalize_modes` / `resolve_normalize_spec()`, and `GeneratedImage.normalize_spec` for per-band-image overrides (spec §13.4). Settings only; stored samples are never normalized
- `Measurement.is_scratch` flags uncommitted batch outputs carrying the SDK `Scratch` marker; they are still listed

### Changed
- `FLPTIRImage` is now a marker mixin, like `FLPTIRImageStack`. Legacy rank-3 instances still satisfy `isinstance(m, ByteImage2D)`; rank-2 instances satisfy `isinstance(m, FloatImage2D)`; both satisfy `isinstance(m, FLPTIRImage)`
- `TYPE_TO_SHAPE[MeasurementType.FLPTIRImage]` is now `DataShape.FLOAT_IMAGE_2D` (was `BYTE_IMAGE_2D`), matching the current rank-2 layout. As with `FLPTIRImageStack`, it is only a default: each instance's `data_shape` reflects its actual storage, so legacy rank-3 images report `BYTE_IMAGE_2D`

### Fixed
- `FLPTIRImage` now reads the canonical rank-2 `float32` layout that current PTIR Studio versions write, and the older rank-2 `uint16`/`uint8` layouts. Previously these files were typed as byte images and `bytes_per_pixel` raised `IndexError`. `data_float32` returns `(H, W)` float32 for every layout, and `pixel_format` on rank-2 images resolves the camera format as the SDK does (the stored `PixelFormat` for `float32` samples, else `Gray32Float`; `Gray16`/`Gray8` for `uint16`/`uint8` samples); unsupported layouts raise `InvalidMeasurementError`
- Non-UTF-8 bytes in a string attribute no longer abort metadata loading; they decode as U+FFFD. This covers both fixed-length strings and variable-length strings, which h5py returns surrogate-escaped and which would otherwise fail when printed or encoded
- `write_image_stack_result` no longer copies the source's noise-frame link (`NoiseFrameID`, `NoiseFrameCorrectionAppliedAtWrite`, `NoiseFrameCorrectionDisplayEnabled`) onto the derived stack. Inheriting it made PTIR Studio add the source noise frame onto derived values when display correction was off
- Tree `NODES` rows naming a GUID with no `/TREE` group, or with a group that has no `TYPE` attribute (as an interrupted attach or detach can leave), and folder cycles are skipped instead of raising `KeyError` / `RecursionError` (spec §14.5)

## [0.1.1] - 2026-06-12

### Added
- Slice-based dataset reading (`read_dataset_slice`) to avoid loading full arrays for helper methods
- Validation for TREE/NODES data (shape and dtype checks)
- Tests for malformed inputs, PixelFormat resolution, and slice-based reading
- CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md
- GitHub issue and pull request templates
- CI testing on Python 3.11, 3.12, and 3.13
- `ImageStack3D` abstract base for 2D image stacks (parent of `ByteImageStack3D` and `FloatImageStack3D`)
- `FloatImageStack3D` base class for rank-3 float image stacks
- `FLPTIRImageStack.data_float32` and `FLPTIRImageStack.is_legacy` properties
- conda-forge packaging recipe under `packaging/conda-forge/`
- conda-forge installation instructions and badge in README

### Changed
- `FloatHypercube3D.read_spectrum()`, `FloatHypercube3D.read_image()`, and `ByteImageStack3D.read_image()` now use slice reads instead of loading full arrays
- Runtime `assert` statements in `_reader.py` replaced with typed `InvalidMeasurementError` exceptions

### Fixed
- `FLPTIRImageStack` now correctly reads both supported on-disk formats (legacy rank-4 uint8 and new rank-3 float32). Previously, rank-3 float files could not be opened, and rank-4 legacy files returned raw bytes (`(N, H, W, 4) uint8`) instead of the float32 imagery they actually encode. `read_image()` now returns canonical `(H, W) float32` regardless of storage format. The raw on-disk dataset remains available via the `data` property. Legacy stacks continue to satisfy `isinstance(m, ByteImageStack3D)`; rank-3 stacks satisfy `isinstance(m, FloatImageStack3D)`; both satisfy `isinstance(m, ImageStack3D)` and `isinstance(m, FLPTIRImageStack)`.
- Malformed FLPTIRImageStack DATA datasets now raise a typed `InvalidMeasurementError` at the earliest possible point rather than leaking raw numpy errors or returning meaningless data. Rank-4 datasets are validated as `uint8` with trailing dim 4 before bytes are reinterpreted as float32. Rank-3 datasets are validated as `float32` at file-open time so a non-float dataset can never reach the rank-3 read path.

### Removed
- Unused `_NON_ATTR_ITEMS` constant

### Documentation
- Documented the `FLPTIRImageStack` dual-format storage (legacy rank-4 uint8 vs. rank-3 float32), the canonical `data_float32` / `read_image()` float32 contract, and the new `ImageStack3D` / `FloatImageStack3D` base classes in `README.md`, `docs/data_types.md`, and `docs/api_reference.md`
- Added `docs/roadmap.md` for forward-looking work (selective read APIs, CLI tool, ecosystem adapters)
- Removed `docs/release_checklist.md` and `docs/public_release_readiness.md`. They were point-in-time pre-public-release planning artifacts; ongoing work belongs in `CHANGELOG.md` and the issue tracker, roadmap items in `docs/roadmap.md`
- Updated stale test count in `CLAUDE.md`

## [0.1.0] - 2026-02-19

### Added
- Initial release
- Read-only access to all 16 PTIR5 measurement types
- Hierarchical tree navigation
- Flat measurement enumeration with type filtering and GUID lookup
- Background spectra access
- Generated data (ROI spectra, band images) support
- Lazy loading of measurement data and metadata
- Dict-like metadata access with Python-native types
