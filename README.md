# ptir5

Read-only Python library for PTIR5 files — the HDF5-based native format of
[Photothermal Spectroscopy Corp.'s](https://www.photothermal.com/) PTIR Studio
software (v5.0+).

## Installation

```bash
pip install ptir5
```

For local development and testing:

```bash
pip install -e .[dev]
pytest -q
```

## Quick Start

```python
import ptir5

with ptir5.open("sample.ptir") as f:
    # List all measurements
    for m in f.measurements:
        print(m.label, m.measurement_type, m.data.shape)

    # Access a specific spectrum
    spec = f.measurements[0]
    x = spec.x_values        # wavenumber axis
    y = spec.data             # signal values

    # Navigate the document tree
    if f.tree:
        for node, folders, leaves in f.tree.walk():
            for leaf in leaves:
                print(leaf.name, leaf.measurement.data.shape)
```

## Features

- **Read-only access** to all PTIR5 measurement types as numpy arrays
- **16 measurement types**: O-PTIR spectra/images/hyperspectra, Raman spectra/hyperspectra, camera images, fluorescence images, FL-PTIR images, PTSRS spectra/images, and image stacks
- **Hierarchical tree navigation** matching PTIR Studio's document structure
- **Flat measurement enumeration** with type filtering and GUID lookup
- **Background spectra** access
- **Generated data** (ROI spectra, band images) from hyperspectral measurements
- **Lazy loading** — data is read from disk only when accessed
- **Dict-like metadata** with Python-native types

## Data Types

| Type | Class | Array Shape | Dtype |
|------|-------|-------------|-------|
| O-PTIR Spectrum | `OPTIRSpectrum` | `(points,)` | float32 |
| Raman Spectrum | `RamanSpectrum` | `(points,)` | float32 |
| Generated Spectrum | `GeneratedSpectrum` | `(points,)` | float32 |
| PTSRS Spectrum | `PTSRSSpectrum` | `(points,)` | float32 |
| O-PTIR Image | `OPTIRImage` | `(height, width)` | float32 |
| Generated Image | `GeneratedImage` | `(height, width)` | float32 |
| PTSRS Image | `PTSRSImage` | `(height, width)` | float32 |
| Camera Image | `CameraImage` | `(height, width, bpp)` | uint8 |
| Fluorescence Image | `FluorescenceImage` | `(height, width, bpp)` | uint8 |
| FL-PTIR Image | `FLPTIRImage` | `(height, width, bpp)` | uint8 |
| O-PTIR Hyperspectra | `OPTIRHyperspectra` | `(points, height, width)` | float32 |
| Raman Hyperspectra | `RamanHyperspectra` | `(points, height, width)` | float32 |
| O-PTIR Image Stack | `OPTIRImageStack` | `(images, height, width)` | float32 |
| PTSRS Image Stack | `PTSRSImageStack` | `(images, height, width)` | float32 |
| Camera Image Stack | `CameraImageStack` | `(images, height, width, bpp)` | uint8 |
| FL-PTIR Image Stack | `FLPTIRImageStack` | `(images, height, width, bpp)` | uint8 |

## Requirements

- Python >= 3.11
- h5py >= 3.9
- numpy >= 1.24

## License

MIT
