# Data Types

## 5 Fundamental Shapes

Every PTIR5 measurement falls into one of five fundamental data shapes:

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
- **Use**: Hyperspectral data and float image stacks
- **Properties**: `num_points`, `pixel_width`, `pixel_height`, `x_values`
- **Methods**: `read_spectrum(x, y)`, `read_image(index)`

### ByteImageStack3D
- **Array**: `(images, height, width, bytes_per_pixel)` of `uint8`
- **Use**: Camera and FL-PTIR image stacks
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
| `FLPTIRImageStack` | ByteImageStack3D | `ptir5.FLPTIRImageStack` |

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
