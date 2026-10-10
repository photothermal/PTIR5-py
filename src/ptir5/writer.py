"""Non-destructive derived image-stack output; existing file access stays read-only."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import numpy as np

from ptir5._reader import append_stack_result
from ptir5.file import PTIR5File
from ptir5.models import OPTIRImageStack

if TYPE_CHECKING:
    from collections.abc import Mapping


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_image_stack_result(
    source: str | Path,
    output: str | Path,
    measurement_guid: str,
    data: np.ndarray[Any, Any],
    *,
    frame_start: int = 0,
    label: str,
    provenance: Mapping[str, Any],
    expected_source_sha256: str | None = None,
) -> str:
    """Copy a PTIR5 document and append a finite float32 O-PTIR image stack.

    Returns the new measurement GUID. ``data`` is (frames, height, width),
    covering a contiguous frame range and the source's entire spatial area.
    Source measurements, backgrounds and tree nodes are retained. Existing output
    paths are refused; incomplete writes never appear at the final output path.
    Generated children are not copied to the result; extrema are recomputed.
    ``expected_source_sha256`` optionally binds output to an earlier source export.
    Acquisition metadata is inherited and labelled as source context in provenance.
    This is a narrow derived-output API, not a general PTIR5 editor.
    """
    source_path, output_path = Path(source).resolve(), Path(output).absolute()
    if output_path.exists():
        raise FileExistsError(f"Output already exists: {output_path}")
    if not isinstance(label, str) or not label.strip() or "\x00" in label:
        raise ValueError("A nonempty result label without NUL characters is required")
    if isinstance(frame_start, bool) or not isinstance(frame_start, int) or frame_start < 0:
        raise ValueError("frame_start must be a nonnegative integer")
    # Snapshot the caller's data before validation and writing.
    cube = np.array(data, copy=True)
    if cube.dtype != np.float32 or cube.ndim != 3 or min(cube.shape) < 1:
        raise ValueError("Result must be a nonempty rank-3 float32 array")
    if not np.isfinite(cube).all():
        raise ValueError("Derived result must contain only finite values")
    # A same-directory temporary and exclusive hard link make completion atomic
    # without replacing an output created by another process during processing.
    # The private copy is the snapshot: it is validated, hashed and extended, so a
    # source replaced after this point cannot be published as a different acquisition.
    fd, temporary_name = tempfile.mkstemp(
        prefix=".ptir5-result-", suffix=".ptir", dir=output_path.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        # Read mode and bytes from one open file so a path replaced afterwards cannot
        # give the snapshot another file's permissions.
        with source_path.open("rb") as stream, temporary.open("wb") as snapshot:
            source_mode = stat.S_IMODE(os.fstat(stream.fileno()).st_mode)
            shutil.copyfileobj(stream, snapshot)
        source_hash = _sha256(temporary)
        if expected_source_sha256 is not None and source_hash != expected_source_sha256:
            raise ValueError("Source checksum does not match the expected acquisition")
        with PTIR5File(temporary) as document:
            measurement = document.get_measurement(measurement_guid)
            if not isinstance(measurement, OPTIRImageStack):
                raise ValueError("Only OPTIRImageStack derived output is supported")
            if cube.shape[1:] != (measurement.pixel_height, measurement.pixel_width):
                raise ValueError(
                    "Result must cover the full source spatial area; crops are unsupported"
                )
            stop = frame_start + cube.shape[0]
            if stop > measurement.num_points:
                raise ValueError("Result frame range exceeds the source stack")
            metadata = measurement.metadata
            if not all(key in metadata for key in ("XStart", "XIncrement", "XUnits")):
                raise ValueError("Source requires explicit regular wavenumber-axis metadata")
            if metadata["XUnits"] not in ("cm-1", "cm^-1", "cm⁻¹"):
                raise ValueError("Source must have a wavenumber axis")
            start, increment = float(metadata["XStart"]), float(metadata["XIncrement"])
            if not np.isfinite([start, increment]).all() or increment == 0:
                raise ValueError("Source requires finite, nonzero wavenumber-axis metadata")
            coordinates = measurement.x_values[frame_start:stop]
        new_guid = str(uuid4())
        record = {
            "schema_version": 1,
            "source_sha256": source_hash,
            "source_measurement_guid": measurement_guid,
            "result_measurement_guid": new_guid,
            "source_frame_range": [frame_start, stop],
            "spatial_coverage": "full source image",
            "acquisition_metadata_scope": "inherited source acquisition context",
            "processing": dict(provenance),
        }
        record_text = json.dumps(record, ensure_ascii=False, allow_nan=False)
        append_stack_result(
            temporary,
            measurement_guid,
            new_guid,
            cube,
            frame_start,
            label,
            record_text,
            str(output_path),
        )
        with PTIR5File(temporary) as saved:
            result = saved.get_measurement(new_guid)
            if not isinstance(result, OPTIRImageStack):
                raise ValueError("Saved result has an unexpected measurement type")
            np.testing.assert_array_equal(result.data, cube)
            # XStart/XIncrement are stored attributes, so allow float32 rounding of the axis.
            axis_scale = max(float(np.max(np.abs(coordinates))), 1.0)
            axis_tolerance = 4 * np.finfo(np.float32).eps * axis_scale
            if not np.allclose(result.x_values, coordinates, rtol=0.0, atol=axis_tolerance):
                raise ValueError("Saved result axis does not match the source frames")
            if saved.tree is None or not any(
                leaf.guid == new_guid for _, _, leaves in saved.tree.walk() for leaf in leaves
            ):
                raise ValueError("Saved result is missing its document-tree entry")
        # mkstemp creates 0600; match the source's mode only now, so a read-only source
        # cannot make the temporary unwritable while it is still being built.
        os.chmod(temporary, source_mode)
        os.link(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)
    return new_guid
