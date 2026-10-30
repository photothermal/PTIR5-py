# CLAUDE.md

## Project Overview

**ptir5** is a read-only Python library for PTIR5 files — the HDF5-based native format of Photothermal Spectroscopy Corp.'s PTIR Studio software (v5.0+). It provides access to measurement data as numpy arrays.

## Build & Test Commands

```bash
pip install -e ".[dev]"       # Install in dev mode
python -m pytest tests/ -v    # Run all tests (224 tests; 2 POSIX-permission writer tests skip on Windows)
python -m ruff check src/ tests/  # Lint
python -m mypy src/ptir5/     # Type check (strict mode)
```

## Architecture

```
__init__.py → file.py → _reader.py → h5py
                │            │
                ▼            ▼
             tree.py     models.py → numpy
                │            │
                ▼            ▼
           metadata.py    enums.py
                          exceptions.py
```

- **`_reader.py`** is the only module that imports `h5py`. All other modules work with Python-native types and numpy arrays.
- **Lazy loading**: file open reads nothing; `f.measurements` reads GUIDs/types; `m.data` reads the array on demand (not cached); `m.metadata["key"]` loads all attributes on first access (cached).

## Key Design Decisions

- **OPTIRImageStack/PTSRSImageStack** use `FloatHypercube3D` (not `ByteImageStack3D`) because actual data is `(images, height, width) float32`, same layout as hyperspectra. They are not `HyperspectralCube`s, and their `component_completion` is per frame.
- **HyperspectralCube** (`OPTIRHyperspectra`, `RamanHyperspectra`, `TimeDomainCube`) mirrors the SDK's `HyperspectralArrayData` and carries the normalization *settings* (spec §13.4). ptir5 never applies display-time corrections (normalization, PT-SRS power, noise-frame add-back, FL-PTIR background scale); stored samples are returned as stored.
- **FLPTIRImage and FLPTIRImageStack are dual-format** marker mixins. `build_measurement` picks the concrete class from the dataset rank/dtype (image: rank-2 float32/uint16/uint8 or legacy rank-3 bytes; stack: rank-3 float32 or legacy rank-4 bytes), and `data_float32` is the canonical pixel API.
- **Side datasets** next to `DATA` are exposed through `m.auxiliary` (read per access, never cached).
- The format spec is `AGENT2-ptir-studio/src/pc/modules/ptir.file.api/docs/ptir5-file-format.md`, and `PSC.PTIR5.SDK` is authoritative where the spec is silent (e.g. time-domain types).
- **Metadata sub-groups** (Channel, ParticleData, ROIData, Palette) are flattened with dot-prefix: `Channel.Units`, `ROIData.ROIType`.
- **TREE NODES** are stored as `(N, 16) uint8` arrays decoded via `uuid.UUID(bytes_le=...)`.
- **Unknown TYPE values** fall back to a generic `Measurement` with shape inferred from dataset rank and dtype.

## File Layout

- `src/ptir5/` — Library source (10 modules + py.typed)
- `tests/` — Pytest test suite
- `tests/fixtures/` — 8 sample .ptir files from the C# SDK test project
- `docs/` — Markdown documentation
- `examples/` — Runnable example scripts