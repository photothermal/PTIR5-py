# API Reference

## Top-level Functions

### `ptir5.open(path) -> PTIR5File`

Open a PTIR5 file for reading. Returns a `PTIR5File` context manager.

```python
with ptir5.open("sample.ptir") as f:
    ...
```

## PTIR5File

The main entry point for accessing PTIR5 file contents.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `path` | `str` | File path |
| `is_open` | `bool` | Whether the file is currently open |
| `measurements` | `tuple[Measurement, ...]` | All measurements (cached) |
| `backgrounds` | `tuple[Measurement, ...]` | Background spectra (cached) |
| `has_tree` | `bool` | Whether `/TREE` group exists |
| `tree` | `TreeRoot \| None` | Document tree or None |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_measurement(guid)` | `Measurement` | Find measurement by GUID |
| `get_background(guid)` | `Measurement` | Find background by GUID |
| `measurements_by_type(type_)` | `tuple[Measurement, ...]` | Filter by MeasurementType |
| `close()` | `None` | Close the file |

## Measurement (base class)

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `guid` | `str` | HDF5 group name (GUID) |
| `measurement_type` | `MeasurementType \| str` | TYPE attribute |
| `data_shape` | `DataShape` | Fundamental data shape |
| `label` | `str` | Shortcut for `metadata["Label"]` |
| `metadata` | `MetadataView` | Dict-like attribute access |
| `generated` | `tuple[Measurement, ...]` | Child GENERATED items |
| `data` | `np.ndarray` | DATA dataset (read on each access) |

## FloatSpectrum1D

Inherits from `Measurement`. 1D float spectrum `(length,)`.

| Property | Type | Description |
|----------|------|-------------|
| `num_points` | `int` | Number of spectral points |
| `x_start` | `float` | Starting x-axis value |
| `x_increment` | `float` | Step between x points |
| `x_values` | `np.ndarray` | Computed x-axis array |

## FloatImage2D

Inherits from `Measurement`. 2D float image `(height, width)`.

| Property | Type | Description |
|----------|------|-------------|
| `pixel_width` | `int` | Width in pixels |
| `pixel_height` | `int` | Height in pixels |
| `image_width_um` | `float` | Physical width in microns |
| `image_height_um` | `float` | Physical height in microns |

## ByteImage2D

Inherits from `Measurement`. Byte image `(height, width, bpp)`.

| Property | Type | Description |
|----------|------|-------------|
| `pixel_width` | `int` | Width in pixels |
| `pixel_height` | `int` | Height in pixels |
| `bytes_per_pixel` | `int` | Bytes per pixel |
| `pixel_format` | `PixelFormat \| str` | Pixel format enum |
| `image_width_um` | `float` | Physical width in microns |
| `image_height_um` | `float` | Physical height in microns |

## FloatHypercube3D

Inherits from `Measurement`. 3D float cube `(points, height, width)`.

| Property / Method | Type | Description |
|----------|------|-------------|
| `num_points` | `int` | Number of spectral points |
| `pixel_width` | `int` | Width in pixels |
| `pixel_height` | `int` | Height in pixels |
| `image_width_um` | `float` | Physical width in microns |
| `image_height_um` | `float` | Physical height in microns |
| `x_start` | `float` | Starting x-axis value |
| `x_increment` | `float` | Step between x points |
| `x_values` | `np.ndarray` | Computed x-axis array |
| `read_spectrum(x, y)` | `np.ndarray` | Spectrum at pixel (x, y) |
| `read_image(index)` | `np.ndarray` | Image at spectral index |

## ByteImageStack3D

Inherits from `Measurement`. Byte image stack `(images, height, width, bpp)`.

| Property / Method | Type | Description |
|----------|------|-------------|
| `num_images` | `int` | Number of images |
| `pixel_width` | `int` | Width in pixels |
| `pixel_height` | `int` | Height in pixels |
| `bytes_per_pixel` | `int` | Bytes per pixel |
| `pixel_format` | `PixelFormat \| str` | Pixel format enum |
| `image_width_um` | `float` | Physical width in microns |
| `image_height_um` | `float` | Physical height in microns |
| `read_image(index)` | `np.ndarray` | Image at stack index |

## MetadataView

Dict-like read-only mapping over HDF5 group attributes. Implements `collections.abc.Mapping[str, Any]`.

Supports: `dict()`, `.keys()`, `.values()`, `.items()`, `.get()`, `in` operator, `len()`.

Attributes from sub-groups (Channel, ParticleData, ROIData, Palette) are prefixed with the sub-group name: `Channel.Units`, `ROIData.ROIType`, etc.

## Tree Classes

### TreeRoot

| Property / Method | Type | Description |
|----------|------|-------------|
| `children` | `tuple[TreeFolder \| TreeLeaf, ...]` | Direct children |
| `folders` | `tuple[TreeFolder, ...]` | Folder children only |
| `leaves` | `tuple[TreeLeaf, ...]` | Leaf children only |
| `walk()` | `Iterator[...]` | Walk tree top-down |

### TreeFolder

| Property / Method | Type | Description |
|----------|------|-------------|
| `name` | `str` | Folder display name |
| `children` | `tuple[TreeFolder \| TreeLeaf, ...]` | Direct children |
| `folders` | `tuple[TreeFolder, ...]` | Folder children only |
| `leaves` | `tuple[TreeLeaf, ...]` | Leaf children only |
| `walk()` | `Iterator[...]` | Walk subtree top-down |

### TreeLeaf

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Leaf display name |
| `guid` | `str` | Measurement GUID |
| `measurement` | `Measurement \| None` | Resolved measurement |

## Enums

### MeasurementType (StrEnum)

`OPTIRSpectrum`, `RamanSpectrum`, `GeneratedSpectrum`, `PTSRSSpectrum`,
`OPTIRImage`, `GeneratedImage`, `PTSRSImage`, `CameraImage`,
`FluorescenceImage`, `FLPTIRImage`, `OPTIRHyperspectra`, `RamanHyperspectra`,
`OPTIRImageStack`, `CameraImageStack`, `FLPTIRImageStack`, `PTSRSImageStack`

### DataShape (Enum)

`FLOAT_SPECTRUM_1D`, `FLOAT_IMAGE_2D`, `BYTE_IMAGE_2D`, `FLOAT_HYPERCUBE_3D`, `BYTE_IMAGE_STACK_3D`

### PixelFormat (IntEnum)

`Gray8`, `Gray16`, `Rgb24`, `Bgra32`, `Gray32Float`, etc.

## Exceptions

| Exception | Inherits | Description |
|-----------|----------|-------------|
| `PTIR5Error` | `Exception` | Base exception |
| `FileClosedError` | `PTIR5Error` | File is closed |
| `InvalidMeasurementError` | `PTIR5Error` | Invalid measurement data |
| `MeasurementNotFoundError` | `PTIR5Error, KeyError` | GUID not found |
