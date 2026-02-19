# Tree Navigation

PTIR5 files support two ways to access measurements:

## Flat Access (Measurements)

The `measurements` property provides a flat tuple of all measurements:

```python
with ptir5.open("sample.ptir") as f:
    for m in f.measurements:
        print(m.label, m.measurement_type)

    # Filter by type
    spectra = f.measurements_by_type(ptir5.MeasurementType.OPTIRSpectrum)

    # Lookup by GUID
    m = f.get_measurement("793f968a-c62c-4988-bb4b-ecdd5152dca0")
```

## Hierarchical Access (Tree)

The `tree` property provides PTIR Studio's document tree:

```python
with ptir5.open("sample.ptir") as f:
    if f.tree is None:
        print("No tree in this file")
        return

    # Direct children
    for child in f.tree.children:
        if isinstance(child, ptir5.TreeFolder):
            print(f"Folder: {child.name}")
        elif isinstance(child, ptir5.TreeLeaf):
            print(f"Leaf: {child.name} -> {child.measurement.measurement_type}")

    # Walk the whole tree (like os.walk)
    for node, folders, leaves in f.tree.walk():
        name = getattr(node, "name", "ROOT")
        indent = "  "
        for folder in folders:
            print(f"{indent}{name}/{folder.name}/")
        for leaf in leaves:
            print(f"{indent}{name}/{leaf.name}")
```

## Tree Structure

```
TreeRoot
├── TreeFolder("Video Images")
│   ├── TreeLeaf("Camera 1") -> CameraImage
│   └── TreeLeaf("Camera 2") -> CameraImage
├── TreeFolder("O-PTIR Spectra")
│   └── TreeLeaf("Spectrum 1") -> OPTIRSpectrum
└── TreeLeaf("Quick Scan") -> OPTIRImage
```

- **TreeRoot**: The root container (no name)
- **TreeFolder**: Named folder containing children
- **TreeLeaf**: Named leaf pointing to a measurement via GUID

## Folder Convenience Properties

```python
folder = f.tree.folders[0]     # first folder child
folder.folders                  # sub-folders only
folder.leaves                   # leaves only
folder.children                 # all children (folders + leaves)
```
