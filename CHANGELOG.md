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

### Changed
- `FloatHypercube3D.read_spectrum()`, `FloatHypercube3D.read_image()`, and `ByteImageStack3D.read_image()` now use slice reads instead of loading full arrays
- Runtime `assert` statements in `_reader.py` replaced with typed `InvalidMeasurementError` exceptions

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
