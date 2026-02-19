# Examples

## List All Measurements

```python
import ptir5

with ptir5.open("sample.ptir") as f:
    for m in f.measurements:
        print(f"{m.label}: {m.measurement_type} {m.data_shape.value}")
        print(f"  Data shape: {m.data.shape}, dtype: {m.data.dtype}")
        print(f"  Metadata keys: {len(m.metadata)}")
```

## Read and Plot a Spectrum

```python
import ptir5

with ptir5.open("sample.ptir") as f:
    for m in f.measurements:
        if isinstance(m, ptir5.FloatSpectrum1D):
            print(f"Spectrum: {m.label}")
            print(f"  Points: {m.num_points}")
            print(f"  X range: {m.x_start} to {m.x_values[-1]}")
            print(f"  Units: {m.metadata.get('XUnits', 'unknown')}")
            # m.x_values and m.data are numpy arrays ready for plotting
```

## Read and Display an Image

```python
import ptir5

with ptir5.open("sample.ptir") as f:
    for m in f.measurements:
        if isinstance(m, ptir5.FloatImage2D):
            print(f"Image: {m.label}")
            print(f"  Pixels: {m.pixel_width} x {m.pixel_height}")
            print(f"  Physical: {m.image_width_um:.1f} x {m.image_height_um:.1f} um")
            # m.data is a 2D numpy array ready for imshow()

        elif isinstance(m, ptir5.ByteImage2D):
            print(f"Camera: {m.label}")
            print(f"  Pixels: {m.pixel_width} x {m.pixel_height}")
            print(f"  Format: {m.pixel_format}, BPP: {m.bytes_per_pixel}")
```

## Extract Spectra from Hyperspectral Data

```python
import ptir5

with ptir5.open("sample.ptir") as f:
    for m in f.measurements:
        if isinstance(m, ptir5.FloatHypercube3D):
            print(f"Hyperspectral: {m.label}")
            print(f"  Cube: {m.num_points} points x {m.pixel_height} x {m.pixel_width}")

            # Extract spectrum at center pixel
            cx, cy = m.pixel_width // 2, m.pixel_height // 2
            spectrum = m.read_spectrum(cx, cy)
            print(f"  Center spectrum shape: {spectrum.shape}")

            # Extract image at first spectral point
            image = m.read_image(0)
            print(f"  First image shape: {image.shape}")
```

## Browse Generated Data

```python
import ptir5

with ptir5.open("sample.ptir") as f:
    for m in f.measurements:
        if m.generated:
            print(f"{m.label} has {len(m.generated)} generated items:")
            for g in m.generated:
                print(f"  {g.label}: {type(g).__name__} {g.data.shape}")
```

## Access Background Spectra

```python
import ptir5

with ptir5.open("sample.ptir") as f:
    for bg in f.backgrounds:
        print(f"Background: {bg.label}")
        print(f"  Points: {bg.data.shape[0]}")
```

## Inspect Metadata

```python
import ptir5

with ptir5.open("sample.ptir") as f:
    m = f.measurements[0]
    # Print all metadata as a dict
    for key, value in sorted(m.metadata.items()):
        print(f"  {key}: {value}")
```
