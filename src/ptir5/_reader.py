"""Low-level HDF5 access — the only module that imports h5py."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import h5py  # type: ignore[import-untyped]
import numpy as np

from ptir5.exceptions import FileClosedError, InvalidMeasurementError
from ptir5.metadata import MetadataView, _convert_value

if TYPE_CHECKING:
    from pathlib import Path


_KNOWN_SUBGROUPS = frozenset({"Channel", "ParticleData", "ROIData", "Palette"})


class HDF5Reader:
    """Thin wrapper around an h5py.File for read-only PTIR5 access."""

    __slots__ = ("_h5",)

    def __init__(self, path: str | Path) -> None:
        self._h5: h5py.File | None = h5py.File(str(path), "r")

    @property
    def is_open(self) -> bool:
        return self._h5 is not None

    def close(self) -> None:
        if self._h5 is not None:
            self._h5.close()
            self._h5 = None

    def _file(self) -> h5py.File:
        if self._h5 is None:
            raise FileClosedError("PTIR5 file is closed")
        return self._h5

    # -- Group access -------------------------------------------------------

    def has_group(self, path: str) -> bool:
        return path in self._file() and isinstance(self._file()[path], h5py.Group)

    def list_subgroups(self, path: str) -> list[str]:
        """Return names of sub-groups (not datasets) under *path*."""
        grp = self._file()[path]
        return [k for k in grp if isinstance(grp[k], h5py.Group)]

    def list_datasets(self, path: str) -> list[str]:
        """Return names of datasets (not sub-groups) directly under *path*."""
        grp = self._file()[path]
        return [k for k in grp if isinstance(grp[k], h5py.Dataset)]

    # -- Attribute reading --------------------------------------------------

    def read_type(self, path: str) -> str:
        """Read the TYPE attribute from a group."""
        raw = self._file()[path].attrs["TYPE"]
        val = _convert_value(raw)
        if not isinstance(val, str):
            raise InvalidMeasurementError(
                f"Expected str for TYPE attribute, got {type(val).__name__} at {path}"
            )
        return val

    def read_label(self, path: str) -> str:
        """Read the Label attribute, returning '' if missing."""
        grp = self._file()[path]
        if "Label" not in grp.attrs:
            return ""
        val = _convert_value(grp.attrs["Label"])
        if not isinstance(val, str):
            raise InvalidMeasurementError(
                f"Expected str for Label attribute, got {type(val).__name__} at {path}"
            )
        return val

    def build_metadata_view(self, path: str) -> MetadataView:
        """Create a MetadataView that lazily loads all attributes from *path*."""

        def load() -> dict[str, Any]:
            return self._read_all_attrs(path)

        return MetadataView(load)

    def _read_all_attrs(self, path: str) -> dict[str, Any]:
        """Read all attributes from a group and its known sub-groups."""
        grp = self._file()[path]
        result: dict[str, Any] = {}
        # Direct attributes
        for key in grp.attrs:
            result[key] = _convert_value(grp.attrs[key])
        # Sub-group attributes (flattened with prefix)
        for sub_name in _KNOWN_SUBGROUPS:
            if sub_name in grp and isinstance(grp[sub_name], h5py.Group):
                sub = grp[sub_name]
                for key in sub.attrs:
                    result[f"{sub_name}.{key}"] = _convert_value(sub.attrs[key])
        return result

    # -- Dataset reading ----------------------------------------------------

    def _get_dataset(self, path: str) -> h5py.Dataset:
        """Return the h5py.Dataset at *path*, raising on type mismatch."""
        ds = self._file()[path]
        if not isinstance(ds, h5py.Dataset):
            raise InvalidMeasurementError(f"Expected Dataset, got {type(ds).__name__} at {path}")
        return ds

    def read_dataset(self, path: str) -> np.ndarray[Any, Any]:
        """Read an entire dataset as a numpy array."""
        result: Any = self._get_dataset(path)[()]
        return result  # type: ignore[no-any-return]

    def read_dataset_slice(
        self, path: str, slices: tuple[int | slice, ...]
    ) -> np.ndarray[Any, Any]:
        """Read a slice of a dataset without loading the full array."""
        result: Any = self._get_dataset(path)[slices]
        return result  # type: ignore[no-any-return]

    def dataset_shape(self, path: str) -> tuple[int, ...]:
        shape: Any = self._get_dataset(path).shape
        return shape  # type: ignore[no-any-return]

    def dataset_dtype(self, path: str) -> np.dtype[Any]:
        dtype: Any = self._get_dataset(path).dtype
        return dtype  # type: ignore[no-any-return]

    def has_dataset(self, path: str) -> bool:
        return path in self._file() and isinstance(self._file()[path], h5py.Dataset)

    # -- GUID listing -------------------------------------------------------

    def list_measurement_guids(self) -> list[str]:
        """Return GUIDs of all items under /MEASUREMENTS."""
        if not self.has_group("MEASUREMENTS"):
            return []
        return self.list_subgroups("MEASUREMENTS")

    def list_background_guids(self) -> list[str]:
        """Return GUIDs of all items under /BACKGROUNDS."""
        if not self.has_group("BACKGROUNDS"):
            return []
        return self.list_subgroups("BACKGROUNDS")

    def list_generated_guids(self, measurement_path: str) -> list[str]:
        """Return GUIDs under a measurement's GENERATED sub-group."""
        gen_path = f"{measurement_path}/GENERATED"
        if not self.has_group(gen_path):
            return []
        return self.list_subgroups(gen_path)

    # -- Tree NODES ---------------------------------------------------------

    def read_tree_node_ids(self, path: str) -> list[str]:
        """Read NODES dataset and decode binary GUIDs to strings."""
        nodes_path = f"{path}/NODES"
        if not self.has_dataset(nodes_path):
            return []
        data = self.read_dataset(nodes_path)
        # Validate shape: (N, 16) uint8
        if data.ndim != 2 or data.shape[1] != 16:
            raise InvalidMeasurementError(
                f"Expected NODES shape (N, 16), got {data.shape} at {nodes_path}"
            )
        if data.dtype != np.dtype("uint8"):
            raise InvalidMeasurementError(
                f"Expected NODES dtype uint8, got {data.dtype} at {nodes_path}"
            )
        result: list[str] = []
        for i in range(data.shape[0]):
            raw_bytes = bytes(data[i])
            result.append(str(uuid.UUID(bytes_le=raw_bytes)))
        return result

    def has_tree(self) -> bool:
        return self.has_group("TREE")


def _require_local_objects(root: h5py.Group) -> None:
    """Reject links and out-of-file dataset storage anywhere in the document.

    The copy is hashed and then published as a snapshot, so every retained object
    and every dataset payload must live inside it; a soft or external link, an
    externally stored dataset or a virtual dataset would read another file.
    """
    pending, seen = [root], {root.id}
    while pending:
        group = pending.pop()
        for name in group:
            if not isinstance(group.get(name, getlink=True), h5py.HardLink):
                path = f"{group.name.rstrip('/')}/{name}"
                raise ValueError(f"{path} must be a local object, not a link")
            child = group[name]
            if isinstance(child, h5py.Dataset) and (child.is_virtual or child.external):
                raise ValueError(
                    f"{child.name} must store its data in the file, not externally or virtually"
                )
            if isinstance(child, h5py.Group) and child.id not in seen:
                seen.add(child.id)
                pending.append(child)


def _copy_attributes(source: h5py.Group | h5py.Dataset, target: h5py.Group | h5py.Dataset) -> None:
    """Preserve stored datatypes, including UTF-8 character-set declarations."""
    for name, value in source.attrs.items():
        target.attrs.create(name, value, dtype=source.attrs.get_id(name).dtype)


def _set_utf8_attribute(target: h5py.Group | h5py.File, name: str, value: str) -> None:
    """Write a fixed-size UTF-8 string that the PTIR5 SDK decodes correctly."""
    encoded = value.encode("utf-8")
    if name in target.attrs:
        del target.attrs[name]
    target.attrs.create(name, encoded, dtype=h5py.string_dtype("utf-8", max(1, len(encoded))))


def append_stack_result(
    path: str | Path,
    source_guid: str,
    result_guid: str,
    cube: np.ndarray[Any, Any],
    frame_start: int,
    label: str,
    provenance_json: str,
    output_path: str,
) -> None:
    """Append a validated derived stack to a private temporary document copy.

    Layout follows PSC.PTIR5.SDK FloatImageStack and TreeLeaf: DATA is frame/Y/X,
    extrema exist as both scalar attributes and per-frame datasets, and NODES
    stores Guid.ToByteArray() rows (little-endian GUID bytes).
    """
    with h5py.File(path, "r+") as document:
        if _convert_value(document.attrs.get("DocType")) != "PTIR5":
            raise ValueError("Expected root DocType PTIR5")
        _require_local_objects(document)
        source = document[f"MEASUREMENTS/{source_guid}"]
        frame_count = source["DATA"].shape[0]
        stop = frame_start + cube.shape[0]
        frame_names = {
            "BackgroundScale",
            "BalDetSum",
            "BalDetVoltage",
            "BottomFocus",
            "DcValue",
            "Humidity",
            "MaxValue",
            "MinValue",
            "NumAverages",
            "PumpPower",
            "StokesPower",
            "Temperature",
            "TopFocus",
            "Wavenumber",
            "ComponentCompletion",
        }
        # Reject extensions whose semantics we cannot safely preserve/recompute.
        for name, child in source.items():
            if name == "DATA":
                if child.dtype != np.float32 or child.ndim != 3:
                    raise ValueError("Source DATA must be rank-3 float32")
            elif name in frame_names:
                if not isinstance(child, h5py.Dataset) or child.shape != (frame_count,):
                    raise ValueError(f"Malformed per-frame metadata: {name}")
            elif name in {"Channel", "Palette", "GENERATED"}:
                if not isinstance(child, h5py.Group):
                    raise ValueError(f"Stack child must be a group: {name}")
                # Channel/Palette carry attributes only; nested members could hold
                # per-frame data that a copy would leave stale for a shorter result.
                if name != "GENERATED" and len(child) != 0:
                    raise ValueError(f"{name} must not contain nested members")
            else:
                raise ValueError(f"Unsupported stack child for derived output: {name}")
        if "Wavenumber" in source:
            actual = source["Wavenumber"][frame_start:stop]
            expected = float(_convert_value(source.attrs["XStart"])) + np.arange(
                frame_start, stop
            ) * float(_convert_value(source.attrs["XIncrement"]))
            # Stored wavenumbers are rounded to the dataset dtype, so compare at that precision.
            eps = np.finfo(actual.dtype).eps if actual.dtype.kind == "f" else 0.0
            tolerance = 4 * eps * max(float(np.max(np.abs(expected), initial=0.0)), 1.0)
            if not np.allclose(actual, expected, rtol=0.0, atol=tolerance):
                raise ValueError("Per-frame wavenumbers do not match the regular source axis")
        tree = document.require_group("TREE")
        if "NODES" in tree:
            nodes = tree["NODES"][()]
            if nodes.ndim != 2 or nodes.shape[1] != 16 or nodes.dtype != np.uint8:
                raise ValueError("Malformed TREE/NODES")
        else:
            # Do not invent a tree that hides existing measurements.
            raise ValueError("Source requires an existing document tree with TREE/NODES")
        result = document["MEASUREMENTS"].create_group(result_guid)
        _copy_attributes(source, result)
        for name in {"Channel", "Palette"} & set(source):
            document.copy(source[name], result, name=name)
        result.create_dataset(
            "DATA", data=cube, chunks=(1, *cube.shape[1:]), maxshape=(None, *cube.shape[1:])
        )
        for name in frame_names & set(source):
            values = source[name][frame_start:stop]
            if name in {"MinValue", "MaxValue"}:
                values = cube.min(axis=(1, 2)) if name == "MinValue" else cube.max(axis=(1, 2))
            elif name == "ComponentCompletion":
                values = np.ones(cube.shape[0], dtype=np.uint8)
            sliced = result.create_dataset(name, data=values, maxshape=(None,), chunks=True)
            # Units, calibration and extension markers describe the whole dataset.
            _copy_attributes(source[name], sliced)
        for name, values in (
            ("MinValue", cube.min(axis=(1, 2))),
            ("MaxValue", cube.max(axis=(1, 2))),
        ):
            if name not in result:
                result.create_dataset(name, data=values, maxshape=(None,), chunks=True)
            result.attrs[name] = np.array(
                [values.min() if name == "MinValue" else values.max()], dtype=np.float32
            )
        if "GENERATED" in result:
            del result["GENERATED"]
        result.create_group("GENERATED")
        # Palette bounds must describe the new values, not a source display cache.
        for name in ("PaletteMinValue", "PaletteMaxValue"):
            if name in result.attrs:
                del result.attrs[name]
        result.attrs["PaletteAutoRange"] = np.array([1], dtype=np.uint8)
        result.attrs["PaletteAutoRangeToStack"] = np.array([1], dtype=np.uint8)
        # Keep the source attribute's precision so the rebased axis is not coarsened.
        x_start_dtype = np.asarray(source.attrs["XStart"]).dtype
        if x_start_dtype.kind != "f":
            x_start_dtype = np.dtype(np.float64)
        with np.errstate(over="ignore"):
            rebased_start = np.array(
                [
                    float(_convert_value(source.attrs["XStart"]))
                    + frame_start * float(_convert_value(source.attrs["XIncrement"]))
                ],
                dtype=x_start_dtype,
            )
        if not np.isfinite(rebased_start).all():
            raise ValueError("Rebased XStart must be finite in the stored precision")
        result.attrs["XStart"] = rebased_start
        # Assigning replaces fixed-length source strings instead of truncating them.
        _set_utf8_attribute(result, "Label", label)
        _set_utf8_attribute(result, "ProcessingProvenance", provenance_json)
        if "Scratch" in result.attrs:
            del result.attrs["Scratch"]
        _set_utf8_attribute(document, "FilePath", output_path)
        leaf = tree.create_group(result_guid)
        leaf.attrs.create("TYPE", source.attrs["TYPE"], dtype=source.attrs.get_id("TYPE").dtype)
        _set_utf8_attribute(leaf, "Label", label)
        new_row = np.frombuffer(uuid.UUID(result_guid).bytes_le, dtype=np.uint8).reshape(1, 16)
        node_attrs = {
            name: (value, tree["NODES"].attrs.get_id(name).dtype)
            for name, value in tree["NODES"].attrs.items()
        }
        del tree["NODES"]
        replacement = tree.create_dataset(
            "NODES", data=np.concatenate([nodes, new_row]), maxshape=(None, 16), chunks=True
        )
        # Recreating the dataset must not drop attributes attached to the tree index.
        for attr_name, (attr_value, attr_dtype) in node_attrs.items():
            replacement.attrs.create(attr_name, attr_value, dtype=attr_dtype)
        document.flush()
