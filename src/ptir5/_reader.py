"""Low-level HDF5 reader — the only module that imports h5py."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import h5py  # type: ignore[import-untyped]

from ptir5.metadata import MetadataView, _convert_value

if TYPE_CHECKING:
    from pathlib import Path

    import numpy as np


_KNOWN_SUBGROUPS = frozenset({"Channel", "ParticleData", "ROIData", "Palette"})
_NON_ATTR_ITEMS = frozenset({"DATA", "GENERATED", "NODES"})


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
            raise RuntimeError("File is closed")
        return self._h5

    # -- Group access -------------------------------------------------------

    def has_group(self, path: str) -> bool:
        return path in self._file() and isinstance(self._file()[path], h5py.Group)

    def list_subgroups(self, path: str) -> list[str]:
        """Return names of sub-groups (not datasets) under *path*."""
        grp = self._file()[path]
        return [k for k in grp if isinstance(grp[k], h5py.Group)]

    # -- Attribute reading --------------------------------------------------

    def read_type(self, path: str) -> str:
        """Read the TYPE attribute from a group."""
        raw = self._file()[path].attrs["TYPE"]
        val = _convert_value(raw)
        assert isinstance(val, str)
        return val

    def read_label(self, path: str) -> str:
        """Read the Label attribute, returning '' if missing."""
        grp = self._file()[path]
        if "Label" not in grp.attrs:
            return ""
        val = _convert_value(grp.attrs["Label"])
        assert isinstance(val, str)
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

    def read_dataset(self, path: str) -> np.ndarray[Any, Any]:
        """Read an entire dataset as a numpy array."""
        ds = self._file()[path]
        assert isinstance(ds, h5py.Dataset)
        result: Any = ds[()]
        return result  # type: ignore[no-any-return]

    def dataset_shape(self, path: str) -> tuple[int, ...]:
        ds = self._file()[path]
        assert isinstance(ds, h5py.Dataset)
        shape: Any = ds.shape
        return shape  # type: ignore[no-any-return]

    def dataset_dtype(self, path: str) -> np.dtype[Any]:
        ds = self._file()[path]
        assert isinstance(ds, h5py.Dataset)
        dtype: Any = ds.dtype
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
        # Shape: (N, 16) uint8 — each row is a UUID in bytes_le format
        result: list[str] = []
        for i in range(data.shape[0]):
            raw_bytes = bytes(data[i])
            result.append(str(uuid.UUID(bytes_le=raw_bytes)))
        return result

    def has_tree(self) -> bool:
        return self.has_group("TREE")
