# Derived O-PTIR image-stack output

`write_image_stack_result()` creates a new PTIR5 document containing all original
data plus one derived `OPTIRImageStack`. It does not change the source document or
turn `ptir5.open()` into a read/write accessor.

```python
import ptir5

with ptir5.open("source.ptir") as document:
    measurement = document.get_measurement(source_guid)
    selected = measurement.data[0:206]

# Replace selected with a same-shape float32 denoised result when available.
result_guid = ptir5.write_image_stack_result(
    "source.ptir", "result.ptir", source_guid, selected,
    frame_start=0,
    label="DC 1 — SPEND",
    provenance={"method": "SPEND", "run_id": "your-run-id", "settings": {}},
    # Optional checksum from the input export, preventing source substitution:
    expected_source_sha256=source_sha256,
)
```

Only finite rank-3 float32 O-PTIR stacks with explicit regular wavenumber-axis
metadata are supported. Spatial crops, irregular axes, other measurement types
and general editing are outside this API. The result may cover a contiguous
subset of source frames: `frame_start` maps the first result frame to the source;
the result stops at `frame_start + data.shape[0]`. Missing source frames remain
in the original measurement and are never filled or relabelled as denoised.
Stored per-frame wavenumbers, when present, must match the regular axis.

The source's entire document is copied, including backgrounds, original generated
data and tree hierarchy. The new measurement is appended at the tree root with a
new GUID and supplied label. Full spatial coverage retains positions and image
dimensions. Per-frame acquisition metadata is sliced to the selected frame range;
`XStart` is adjusted accordingly. Original acquisition settings/timestamps are
inherited source context, not a claim of a new acquisition. The new measurement's
`ProcessingProvenance` JSON records the source checksum/GUID, result GUID, frame
range and caller's processing record.

Inherited metadata keeps its HDF5 datatype and string character set. New labels,
provenance and file paths are fixed-size UTF-8 attributes. This matters to PTIR
Studio and the .NET SDK, which honor the declared character set: storing UTF-8
bytes as ASCII corrupts units such as `cm⁻¹` and can change spectrum presentation.
Numeric coordinate/value round trips alone do not detect that interoperability bug.

The derived stack has recomputed global/per-frame minima and maxima, automatic
palette ranges, and no copied generated children. Unknown stack child layouts are
rejected instead of copying potentially stale caches. Optional component-completion
values mark all result frames complete. Original noise-correction metadata is
retained; this API applies no correction, scaling or normalization.

Writing uses a private temporary file in the existing output directory, checks
its source checksum, and reopens the result to verify exact values, coordinates
and tree identity. It publishes the completed file with an exclusive hard link,
then removes the temporary name. This requires a filesystem supporting hard links
(validated on NTFS). Existing output files, including the source, are never
overwritten; failures clean up the temporary. The saved `FilePath` points to the
new document.

DC 1 integration validation used the 206 finite frames at 1000–1820 cm⁻¹ from a
538-frame source. Identity and real SPEND results reopened with exact pixels and
coordinates in PTIR5-py and PSC.PTIR5.SDK. Studio's image/spectrum components loaded
the derived data. This establishes format interoperability, not denoising quality.
