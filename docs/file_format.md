# PTIR5 File Format

PTIR5 files are standard HDF5 files (`.ptir` extension) used by Photothermal
Spectroscopy Corp.'s PTIR Studio software (v5.0+).

## HDF5 Structure

```
Root (/)
├── MEASUREMENTS/          (required)
│   └── {GUID}/            one group per measurement
│       ├── DATA           primary dataset
│       ├── Channel/       channel metadata sub-group
│       ├── ParticleData/  particle analysis (optional)
│       ├── GENERATED/     derived data (optional)
│       │   └── {GUID}/    generated measurement groups
│       └── (attributes)   measurement metadata
├── BACKGROUNDS/           (required, may be empty)
│   └── {GUID}/            background spectra
│       ├── DATA           1D float spectrum
│       ├── Channel/       channel metadata
│       └── (attributes)
├── TREE/                  (optional)
│   ├── NODES              root child GUIDs (N x 16 uint8)
│   └── {GUID}/            tree node groups
│       ├── TYPE           "FOLDER" or measurement type
│       ├── Label          display name
│       └── NODES          child GUIDs (for folders)
└── VIEW/                  (optional, PTIR Studio internal)
```

## Naming Conventions

- Required groups/datasets use ALL CAPS: `MEASUREMENTS`, `BACKGROUNDS`, `DATA`, `NODES`
- Optional attributes use PascalCase: `Label`, `ImageWidth`, `XStart`
- Measurement groups are named by GUIDs to prevent collisions

## DATA Dataset Shapes

| Measurement Type | Dimensions | HDF5 Type |
|-----------------|------------|-----------|
| Spectra | (length,) | IEEE_F32LE |
| Float images | (height, width) | IEEE_F32LE |
| Byte images | (height, width, BPP) | STD_U8LE |
| Hyperspectral | (points, height, width) | IEEE_F32LE |
| Byte image stacks | (images, height, width, BPP) | STD_U8LE |
| Float image stacks | (images, height, width) | IEEE_F32LE |

## TREE NODES Encoding

The `NODES` dataset stores child GUIDs as a 2D array of shape `(N, 16)` with
dtype `uint8`. Each row contains 16 bytes representing a UUID in little-endian
byte order (`bytes_le` format). To decode: `uuid.UUID(bytes_le=row_bytes)`.

## Metadata Storage

Attributes are stored directly on measurement HDF5 groups. Sub-groups
(`Channel`, `ParticleData`, `ROIData`, `Palette`) contain their own attributes
for organizing related metadata.

Numeric values are stored as numpy arrays (typically shape `(1,)` for scalars).
String values are stored as byte strings. The ptir5 library automatically
converts these to Python-native types.
