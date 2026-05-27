# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

### Changed
- `FloatHypercube3D.read_spectrum()`, `FloatHypercube3D.read_image()`, and `ByteImageStack3D.read_image()` now use slice reads instead of loading full arrays
- Runtime `assert` statements in `_reader.py` replaced with typed `InvalidMeasurementError` exceptions

### Fixed
- `FLPTIRImageStack` now correctly reads both supported on-disk formats (legacy rank-4 uint8 and new rank-3 float32). Previously, rank-3 float files could not be opened, and rank-4 legacy files returned raw bytes (`(N, H, W, 4) uint8`) instead of the float32 imagery they actually encode. `read_image()` now returns canonical `(H, W) float32` regardless of storage format. The raw on-disk dataset remains available via the `data` property. Legacy stacks continue to satisfy `isinstance(m, ByteImageStack3D)`; rank-3 stacks satisfy `isinstance(m, FloatImageStack3D)`; both satisfy `isinstance(m, ImageStack3D)` and `isinstance(m, FLPTIRImageStack)`.
- Malformed rank-4 FLPTIRImageStack DATA datasets (wrong dtype or trailing dim ≠ 4) now raise a typed `InvalidMeasurementError` instead of leaking a raw numpy `ValueError` or returning meaningless reinterpreted bytes.

### Removed
- Unused `_NON_ATTR_ITEMS` constant

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
