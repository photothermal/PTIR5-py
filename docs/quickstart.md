# Quick Start

## Installation

```bash
pip install ptir5
```

## First Usage

```python
import ptir5

# Open a PTIR5 file
with ptir5.open("sample.ptir") as f:
    # Print all measurements
    for m in f.measurements:
        print(f"{m.label}: {m.measurement_type} {m.data.shape}")
```

## Reading a Spectrum

```python
import ptir5
import matplotlib.pyplot as plt

with ptir5.open("sample.ptir") as f:
    spec = f.measurements[0]  # assuming first measurement is a spectrum
    assert isinstance(spec, ptir5.FloatSpectrum1D)

    plt.plot(spec.x_values, spec.data)
    plt.xlabel(spec.metadata.get("XUnits", ""))
    plt.ylabel(spec.metadata.get("Channel.Units", ""))
    plt.title(spec.label)
    plt.show()
```

## Reading an Image

```python
import ptir5
import matplotlib.pyplot as plt

with ptir5.open("sample.ptir") as f:
    img = f.measurements[0]  # assuming first measurement is an image
    assert isinstance(img, ptir5.FloatImage2D)

    plt.imshow(img.data, aspect="equal")
    plt.title(f"{img.label} ({img.image_width_um:.1f} x {img.image_height_um:.1f} um)")
    plt.colorbar()
    plt.show()
```

## Browsing the Tree

```python
import ptir5

with ptir5.open("sample.ptir") as f:
    if f.tree:
        for node, folders, leaves in f.tree.walk():
            name = getattr(node, "name", "ROOT")
            for leaf in leaves:
                if leaf.measurement is not None:
                    print(f"  {name}/{leaf.name}: {leaf.measurement.measurement_type}")
```
