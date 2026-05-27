# Data Types

## Fundamental Shapes

Every PTIR5 measurement falls into one of five concrete data shapes. Stacks of
2D images additionally share a common abstract base, :class:`ImageStack3D`, so
callers can dispatch on "is this a stack of images" without caring about the
on-disk storage format.

### FloatSpectrum1D
- **Array**: `(length,)` of `float32`
- **Use**: Single-point spectra (O-PTIR, Raman, PTSRS, Generated)
- **Properties**: `num_points`, `x_start`, `x_increment`, `x_values`

### FloatImage2D
- **Array**: `(height, width)` of `float32`
- **Use**: Single-wavenumber images (O-PTIR, Generated, PTSRS)
- **Properties**: `pixel_width`, `pixel_height`, `image_width_um`, `image_height_um`

### ByteImage2D
- **Array**: `(height, width, bytes_per_pixel)` of `uint8`
- **Use**: Camera and fluorescence images
- **Properties**: `pixel_width`, `pixel_height`, `bytes_per_pixel`, `pixel_format`

### FloatHypercube3D
- **Array**: `(points, height, width)` of `float32`
- **Use**: Hyperspectral data and float image stacks where axis 0 is spectral
- **Properties**: `num_points`, `pixel_width`, `pixel_height`, `x_values`
- **Methods**: `read_spectrum(x, y)`, `read_image(index)`

### ImageStack3D (abstract)
- **Use**: Common base for any stack of 2D images (axis 0 is frame index, not
  spectral). Subclasses `ByteImageStack3D` and `FloatImageStack3D` provide the
  concrete storage shape.
- **Properties**: `num_images`, `pixel_width`, `pixel_height`, `pixel_format`,
  `image_width_um`, `image_height_um`

### ByteImageStack3D
- **Inherits**: `ImageStack3D`
- **Array**: `(images, height, width, bytes_per_pixel)` of `uint8`
- **Use**: Camera image stacks and legacy FL-PTIR image stacks
- **Properties**: `num_images`, `pixel_width`, `pixel_height`, `bytes_per_pixel`,
  `pixel_format`
- **Methods**: `read_image(index)`

### FloatImageStack3D
- **Inherits**: `ImageStack3D`
- **Array**: `(images, height, width)` of `float32`
- **Use**: Rank-3 FL-PTIR image stacks (the format newly allocated stacks use)
- **Properties**: `num_images`, `pixel_width`, `pixel_height`, `pixel_format`
- **Methods**: `read_image(index)`

## 16 Concrete Types

| TYPE String | Base Shape | Class |
|-------------|-----------|-------|
| `OPTIRSpectrum` | FloatSpectrum1D | `ptir5.OPTIRSpectrum` |
| `RamanSpectrum` | FloatSpectrum1D | `ptir5.RamanSpectrum` |
| `GeneratedSpectrum` | FloatSpectrum1D | `ptir5.GeneratedSpectrum` |
| `PTSRSSpectrum` | FloatSpectrum1D | `ptir5.PTSRSSpectrum` |
| `OPTIRImage` | FloatImage2D | `ptir5.OPTIRImage` |
| `GeneratedImage` | FloatImage2D | `ptir5.GeneratedImage` |
| `PTSRSImage` | FloatImage2D | `ptir5.PTSRSImage` |
| `CameraImage` | ByteImage2D | `ptir5.CameraImage` |
| `FluorescenceImage` | ByteImage2D | `ptir5.FluorescenceImage` |
| `FLPTIRImage` | ByteImage2D | `ptir5.FLPTIRImage` |
| `OPTIRHyperspectra` | FloatHypercube3D | `ptir5.OPTIRHyperspectra` |
| `RamanHyperspectra` | FloatHypercube3D | `ptir5.RamanHyperspectra` |
| `OPTIRImageStack` | FloatHypercube3D | `ptir5.OPTIRImageStack` |
| `PTSRSImageStack` | FloatHypercube3D | `ptir5.PTSRSImageStack` |
| `CameraImageStack` | ByteImageStack3D | `ptir5.CameraImageStack` |
| `FLPTIRImageStack` | ByteImageStack3D _or_ FloatImageStack3D ([see below](#flptirimagestack--dual-format)) | `ptir5.FLPTIRImageStack` |

## FLPTIRImageStack — dual format

`FLPTIRImageStack` is the only measurement type with two supported on-disk
storage layouts. Both produce the same canonical float32 imagery to callers:

| Storage format | DATA shape | DATA dtype | Concrete base | `is_legacy` |
|----------------|------------|------------|---------------|-------------|
| Legacy rank-4  | `(N, H, W, 4)` | `uint8` (each 4-byte pixel encodes one `float32`) | `ByteImageStack3D` | `True` |
| Rank-3 float   | `(N, H, W)`    | `float32` | `FloatImageStack3D` | `False` |

Either format satisfies `isinstance(m, FLPTIRImageStack)` and
`isinstance(m, ImageStack3D)`. The library picks the concrete class at file-open
time from the actual dataset rank/dtype and rejects any other layout with
`InvalidMeasurementError`.

Regardless of the underlying format:

- **`read_image(index)`** returns the frame as `(height, width)` `float32`.
- **`data_float32`** returns the full stack as `(num_images, height, width)`
  `float32`.
- **`data`** returns the unmodified on-disk dataset — `uint8` for legacy files,
  `float32` for rank-3 files. Use this only if you need the raw bytes; the
  float APIs above are the canonical way to read pixel values.

Use `is_legacy` to disambiguate the storage when it matters (e.g. for diagnostics
or migration tooling); for normal pixel access you should not need to.

## Common Metadata Keys

### Measurement Attributes
- `Label` — Display name
- `TYPE` — Measurement type string
- `Timestamp` — DateTime ticks
- `MachineName` — Instrument name
- `PositionX`, `PositionY` — Stage position (microns)
- `TopFocus` — Z-axis focus (microns)
- `Temperature`, `Humidity` — Environmental readings

### Spectrum Attributes
- `XStart` — Starting x-axis value
- `XIncrement` — Step between points
- `XUnits` — X-axis units (e.g., "cm-1")
- `NumAverages` — Number of averaged scans

### Image Attributes
- `ImageWidth`, `ImageHeight` — Physical size (microns)
- `Wavenumber` — Wavenumber at which image was collected (cm-1)
- `PixelFormat` — Pixel format for byte images

### Channel Sub-group (`Channel.*`)
- `Channel.Units` — Data units (e.g., "mV")
- `Channel.DataSignal` — Signal type
- `Channel.Label` — Channel name
- `Channel.Scale`, `Channel.Offset` — Scale/offset values

### ROI Data Sub-group (`ROIData.*`)
- `ROIData.ROIType` — ROI shape (e.g., "POINT", "CIRCLE")
- `ROIData.PositionX`, `ROIData.PositionY` — ROI center (microns)
- `ROIData.ROIWidth`, `ROIData.ROIHeight` — ROI dimensions (microns)
