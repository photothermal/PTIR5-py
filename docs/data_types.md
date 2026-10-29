# Data Types

## Fundamental Shapes

Every PTIR5 measurement falls into one of five concrete data shapes. Stacks of
2D images additionally share a common abstract base, :class:`ImageStack3D`, so
callers can dispatch on "is this a stack of images" without caring about the
on-disk storage format.

### FloatSpectrum1D
- **Array**: `(length,)` of `float32`
- **Use**: Single-point spectra (O-PTIR, Raman, PTSRS, Generated) and time-domain
  bursts (x-axis in µs)
- **Properties**: `num_points`, `x_start`, `x_increment`, `x_values`

### FloatImage2D
- **Array**: `(height, width)` of `float32`
- **Use**: Single-wavenumber images (O-PTIR, Generated, PTSRS) and rank-2 FL-PTIR
  images (which may store `uint16`/`uint8` pixels; see below)
- **Properties**: `pixel_width`, `pixel_height`, `image_width_um`, `image_height_um`

### ByteImage2D
- **Array**: `(height, width, bytes_per_pixel)` of `uint8`
- **Use**: Camera and fluorescence images, and legacy FL-PTIR images
- **Properties**: `pixel_width`, `pixel_height`, `bytes_per_pixel`, `pixel_format`

### FloatHypercube3D
- **Array**: `(points, height, width)` of `float32`
- **Use**: Hyperspectral data and float image stacks where axis 0 is spectral
- **Properties**: `num_points`, `pixel_width`, `pixel_height`, `x_values`
- **Methods**: `read_spectrum(x, y)`, `read_image(index)`

### HyperspectralCube
- **Inherits**: `FloatHypercube3D`
- **Use**: Cubes holding one spectrum per pixel: O-PTIR and Raman hyperspectra,
  and time-domain cubes (one waveform per pixel, axis 0 in µs). Mirrors the C#
  SDK's `HyperspectralArrayData`. `OPTIRImageStack` and `PTSRSImageStack` share
  the storage shape but are not hyperspectral cubes.

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

## 18 Concrete Types

| TYPE String | Base Shape | Class |
|-------------|-----------|-------|
| `OPTIRSpectrum` | FloatSpectrum1D | `ptir5.OPTIRSpectrum` |
| `RamanSpectrum` | FloatSpectrum1D | `ptir5.RamanSpectrum` |
| `GeneratedSpectrum` | FloatSpectrum1D | `ptir5.GeneratedSpectrum` |
| `PTSRSSpectrum` | FloatSpectrum1D | `ptir5.PTSRSSpectrum` |
| `TimeDomainBurst` | FloatSpectrum1D | `ptir5.TimeDomainBurst` |
| `OPTIRImage` | FloatImage2D | `ptir5.OPTIRImage` |
| `GeneratedImage` | FloatImage2D | `ptir5.GeneratedImage` |
| `PTSRSImage` | FloatImage2D | `ptir5.PTSRSImage` |
| `CameraImage` | ByteImage2D | `ptir5.CameraImage` |
| `FluorescenceImage` | ByteImage2D | `ptir5.FluorescenceImage` |
| `FLPTIRImage` | FloatImage2D _or_ ByteImage2D ([see below](#flptirimage--dual-format)) | `ptir5.FLPTIRImage` |
| `OPTIRHyperspectra` | HyperspectralCube | `ptir5.OPTIRHyperspectra` |
| `RamanHyperspectra` | HyperspectralCube | `ptir5.RamanHyperspectra` |
| `TimeDomainCube` | HyperspectralCube | `ptir5.TimeDomainCube` |
| `OPTIRImageStack` | FloatHypercube3D | `ptir5.OPTIRImageStack` |
| `PTSRSImageStack` | FloatHypercube3D | `ptir5.PTSRSImageStack` |
| `CameraImageStack` | ByteImageStack3D | `ptir5.CameraImageStack` |
| `FLPTIRImageStack` | ByteImageStack3D _or_ FloatImageStack3D ([see below](#flptirimagestack--dual-format)) | `ptir5.FLPTIRImageStack` |

## FLPTIRImage — dual format

Single FL-PTIR images also have two supported on-disk layouts. Both produce
`(height, width)` `float32` imagery through `data_float32`:

| Storage format | DATA shape | DATA dtype | Concrete base | `is_legacy` |
|----------------|------------|------------|---------------|-------------|
| Rank-2 (current) | `(H, W)` | `float32` (`Gray32Float`), `uint16` (`Gray16`) or `uint8` (`Gray8`) | `FloatImage2D` | `False` |
| Legacy rank-3  | `(H, W, 4)` | `uint8` (each 4-byte pixel encodes one `float32`) | `ByteImage2D` | `True` |

As in the C# SDK, the dataset dtype decides the rank-2 pixel format.
`pixel_format` reports the stored `PixelFormat` attribute. `data` returns the
unmodified on-disk dataset. Any other rank or rank-2 dtype raises
`InvalidMeasurementError` when the file's measurements are loaded; a legacy
rank-3 dataset whose trailing dimension is not 4 raises when it is read.

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

## Side Datasets

Per-pixel and per-frame arrays are stored as datasets next to `DATA`. Read them
through `m.auxiliary`, a read-only mapping keyed by dataset name. Each access
reads from the file, and nothing is cached:

```python
wavenumbers = stack.auxiliary["Wavenumber"]      # (images,) float32
averages = cube.auxiliary["NumAverages"]         # (height, width) int32
```

A side dataset can share its name with a scalar attribute on the same group. For example,
`m.auxiliary["NumAverages"]` holds the per-pixel or per-frame counts, while
`m.metadata["NumAverages"]` holds the object-level value. Both may be present.

Which datasets exist depends on the acquisition:

| Owner | Shape | Datasets |
|-------|-------|----------|
| Hyperspectral and time-domain cubes | `(height, width)` | `NumAverages` (int32), `MinValue`, `MaxValue`, `TopFocus`, `BottomFocus`, `Temperature`, `Humidity`, `BaselineNoise`, `DcValue`, `BalDetVoltage`, `BalDetSum`, `ComponentCompletion` (uint8) |
| Image stacks | `(images,)` | `NumAverages` (int32), `TopFocus`, `BottomFocus`, `Wavenumber`, `BackgroundScale`, `MinValue`, `MaxValue`, `Temperature`, `Humidity`, `DcValue`, `BalDetVoltage`, `BalDetSum`, `ComponentCompletion` (uint8) |
| O-PTIR / PT-SRS image stacks | `(images,)` | `PumpPower`, `StokesPower` (mW) |
| PT-SRS image stacks | `(images,)` | `PumpWavelength`, `StokesWavelength` (nm, informational) |

### Component completion

Acquisition software can opt in to recording which components are final: one
flag per pixel spectrum for cubes, one per frame for stacks. The
`component_completion` property on `FloatHypercube3D` and `ImageStack3D` decodes
it:

- `None`: the file does not track completion (normal for older files).
- A `bool` array: `True` where the component is complete, and `False` where it
  is incomplete. Any stored value other than 1 counts as incomplete (fail
  closed).

A completion dataset with the wrong dtype or shape raises
`InvalidMeasurementError`.

## Normalization Settings

PTIR Studio can display a hyperspectral cube, and each band image derived from
it, normalized. The setting is stored in two attributes, `NormalizeMode` and
`NormalizeWavenumber`; the second holds the reference coordinate in the cube's
`XUnits`. **ptir5 reports the setting but never normalizes data:** `data`,
`read_spectrum()` and `read_image()` return the stored samples.

| Cube type | Supported modes |
|-----------|-----------------|
| `OPTIRHyperspectra`, `RamanHyperspectra` | `Off`, `Peak`, `Wavenumber` |
| `TimeDomainCube` | `Off`, `Peak`, `Time`, `Offset` |

- `cube.normalize_spec` returns a `NormalizeSpec(mode, reference)`. A missing,
  unknown or unsupported mode reads as `Off`. Names match case-insensitively.
- `band_image.normalize_spec` is the band image's own setting, or `None` when
  it has none and follows its cube. An explicit `Off` differs from `None`, and
  an unparseable mode reads as `Off`.
- `cube.resolve_normalize_spec(band_image)` returns the effective setting, using
  the rule from spec §13.4:
  - If the image has its own mode, the result uses that mode and only the
    image's own reference; the cube's reference is never used. A mode the cube
    type does not support reads as `Off`.
  - Otherwise the result is the cube's setting.

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

### Acquisition Attributes Added in PTIR Studio 5.1+

All of these are plain attributes, read through `m.metadata[...]`:

| Key | Type | Units / values | Found on |
|-----|------|----------------|----------|
| `AutoFocusMode` | string | auto-focus mode name | O-PTIR and PT-SRS spectra, O-PTIR hyperspectra, and O-PTIR, PT-SRS and FL-PTIR image stacks |
| `AutoFocusWavenumber` | float32 | cm⁻¹ | Same objects as `AutoFocusMode` |
| `NumAverages` | int32 | count | Photothermal scan images and FL-PTIR images. Spectra, cubes and stacks carry the same scalar attribute; cubes and stacks can also store per-component counts in a `NumAverages` side dataset. The two are independent (see [Side Datasets](#side-datasets)) |
| `RepairedPointCount` | int32 | pixels synthesized to repair missing scan lines | Photothermal scan images |
| `PumpWavelength`, `StokesWavelength` | float32 | nm (informational) | PT-SRS spectra and images (per-frame datasets on PT-SRS stacks) |
| `AomModulationFrequency` | float32 | Hz (informational) | PT-SRS spectra, images and stacks |
| `AomModulationDutyCycle` | float32 | % (informational) | PT-SRS spectra, images and stacks |
| `BandIntegrationMode` | string | `TotalArea` or `BaselineArea` | Generated band images |
| `NormalizeMode`, `NormalizeWavenumber` | string, float32 | see [Normalization Settings](#normalization-settings) | Hyperspectral cubes, band images |
| `FrameRate` | float32 | Hz (widefield camera) | FL-PTIR images and stacks |
| `SampleRate` | float64 | Hz | Time-domain bursts and cubes |
| `BurstBackend`, `BurstInputSource` | string | capture backend / input description | Time-domain bursts and cubes |
| `BurstOverflow` | byte | `0`/`1` (data-loss fault) | Time-domain bursts and cubes |
| `NoiseFrameID` | string | GUID of the stored noise-frame image | Photothermal scan images and float image stacks |
| `NoiseFrameCorrectionAppliedAtWrite` | byte | `0`/`1`: stored pixels already have the noise frame subtracted | Photothermal scan images and float image stacks |
| `NoiseFrameCorrectionDisplayEnabled` | byte | `0`/`1`: PTIR Studio display preference | Photothermal scan images and float image stacks |
| `Scratch` | string | non-empty marks an uncommitted output (see `is_scratch`) | Any measurement |
| `ParticleData.ChemIDResult` | string | opaque application-defined envelope, at most 16 KiB UTF-8 | Measurements with particle data |

When `NoiseFrameCorrectionAppliedAtWrite` is `1`, the pixels `data` returns
already have the noise frame subtracted. PTIR Studio adds the frame back only
for display, when display correction is off. ptir5 returns the stored pixels.

### Channel Sub-group (`Channel.*`)
- `Channel.Units` — Data units (e.g., "mV")
- `Channel.DataSignal` — Signal type
- `Channel.Label` — Channel name
- `Channel.Scale`, `Channel.Offset` — Scale/offset values

### ROI Data Sub-group (`ROIData.*`)
- `ROIData.ROIType` — ROI shape (e.g., "POINT", "CIRCLE")
- `ROIData.PositionX`, `ROIData.PositionY` — ROI center (microns)
- `ROIData.ROIWidth`, `ROIData.ROIHeight` — ROI dimensions (microns)
