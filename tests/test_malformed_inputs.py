"""Tests for malformed HDF5 input handling."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import h5py
import numpy as np
import pytest

import ptir5
from ptir5 import InvalidMeasurementError

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    WritePtir = Callable[..., Path]


def _write_minimal_file(path: Path) -> None:
    with h5py.File(path, "w") as h5:
        h5.create_group("MEASUREMENTS")
        h5.create_group("BACKGROUNDS")


class TestMissingTypeAttribute:
    def test_missing_type_raises_key_error(self, tmp_path: Path) -> None:
        path = tmp_path / "no_type.ptir"
        _write_minimal_file(path)
        with h5py.File(path, "a") as h5:
            g = h5["MEASUREMENTS"].create_group("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
            g.create_dataset("DATA", data=np.zeros((8,), dtype=np.float32))
            # No TYPE attribute

        with ptir5.open(path) as f, pytest.raises(KeyError):
            _ = f.measurements


class TestMissingDataDataset:
    def test_missing_data_dataset_still_builds(self, tmp_path: Path) -> None:
        """Unknown type with no DATA falls back to base Measurement."""
        path = tmp_path / "no_data.ptir"
        _write_minimal_file(path)
        with h5py.File(path, "a") as h5:
            g = h5["MEASUREMENTS"].create_group("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
            g.attrs["TYPE"] = np.bytes_(b"UnknownNoData")
            # No DATA dataset

        with ptir5.open(path) as f:
            m = f.measurements[0]
            assert type(m) is ptir5.Measurement
            assert m.measurement_type == "UnknownNoData"


class TestCorruptedTreeNodes:
    def test_wrong_shape_raises(self, tmp_path: Path) -> None:
        """NODES with wrong number of columns should raise."""
        path = tmp_path / "bad_nodes.ptir"
        _write_minimal_file(path)
        with h5py.File(path, "a") as h5:
            tree = h5.create_group("TREE")
            tree.attrs["TYPE"] = np.bytes_(b"ROOT")
            # Wrong shape: (2, 8) instead of (N, 16)
            tree.create_dataset("NODES", data=np.zeros((2, 8), dtype=np.uint8))

        with (
            ptir5.open(path) as f,
            pytest.raises(InvalidMeasurementError, match="Expected NODES shape"),
        ):
            _ = f.tree

    def test_wrong_dtype_raises(self, tmp_path: Path) -> None:
        """NODES with wrong dtype should raise."""
        path = tmp_path / "bad_dtype.ptir"
        _write_minimal_file(path)
        with h5py.File(path, "a") as h5:
            tree = h5.create_group("TREE")
            tree.attrs["TYPE"] = np.bytes_(b"ROOT")
            # Wrong dtype: float32 instead of uint8
            tree.create_dataset("NODES", data=np.zeros((1, 16), dtype=np.float32))

        with (
            ptir5.open(path) as f,
            pytest.raises(InvalidMeasurementError, match="Expected NODES dtype uint8"),
        ):
            _ = f.tree

    def test_1d_nodes_raises(self, tmp_path: Path) -> None:
        """1D NODES array should raise (wrong ndim)."""
        path = tmp_path / "1d_nodes.ptir"
        _write_minimal_file(path)
        with h5py.File(path, "a") as h5:
            tree = h5.create_group("TREE")
            tree.attrs["TYPE"] = np.bytes_(b"ROOT")
            tree.create_dataset("NODES", data=np.zeros((16,), dtype=np.uint8))

        with (
            ptir5.open(path) as f,
            pytest.raises(InvalidMeasurementError, match="Expected NODES shape"),
        ):
            _ = f.tree

    def test_empty_nodes_succeeds(self, tmp_path: Path) -> None:
        """NODES with shape (0, 16) should succeed with empty children."""
        path = tmp_path / "empty_nodes.ptir"
        _write_minimal_file(path)
        with h5py.File(path, "a") as h5:
            tree = h5.create_group("TREE")
            tree.attrs["TYPE"] = np.bytes_(b"ROOT")
            tree.create_dataset("NODES", data=np.zeros((0, 16), dtype=np.uint8))

        with ptir5.open(path) as f:
            assert f.tree is not None
            assert len(f.tree.children) == 0


class TestInvalidDatasetType:
    def test_group_instead_of_dataset_raises(self, tmp_path: Path) -> None:
        """Accessing a group as a dataset should raise InvalidMeasurementError."""
        path = tmp_path / "group_as_dataset.ptir"
        _write_minimal_file(path)
        with h5py.File(path, "a") as h5:
            g = h5["MEASUREMENTS"].create_group("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
            g.attrs["TYPE"] = np.bytes_(b"OPTIRSpectrum")
            g.create_group("DATA")  # Group instead of dataset

        with ptir5.open(path) as f:
            m = f.measurements[0]
            with pytest.raises(InvalidMeasurementError, match="Expected Dataset"):
                _ = m.data


class TestInvalidTypeAttribute:
    def test_non_string_type_raises(self, tmp_path: Path) -> None:
        """Non-string TYPE attribute should raise InvalidMeasurementError."""
        path = tmp_path / "int_type.ptir"
        _write_minimal_file(path)
        with h5py.File(path, "a") as h5:
            g = h5["MEASUREMENTS"].create_group("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
            g.attrs["TYPE"] = 42  # Integer instead of string

        with (
            ptir5.open(path) as f,
            pytest.raises(InvalidMeasurementError, match="Expected str"),
        ):
            _ = f.measurements


def _guid_rows(*guids: str) -> np.ndarray:
    return np.stack([np.frombuffer(uuid.UUID(g).bytes_le, np.uint8) for g in guids])


class TestNonUtf8StringAttribute:
    def test_invalid_bytes_are_replaced_not_fatal(self, write_ptir: WritePtir) -> None:
        path = write_ptir("OPTIRSpectrum", np.zeros(3, np.float32),
                          attrs={"XUnits": np.bytes_(b"\xb5s"), "Label": "ok"})
        with ptir5.open(path) as f:
            m = f.measurements[0]
            assert m.metadata["XUnits"] == "\ufffds"
            assert m.label == "ok"


class TestUnresolvedTreeNodes:
    LEAF = "11111111-2222-3333-4444-555555555555"     # write_ptir's measurement GUID
    MISSING = "99999999-9999-9999-9999-999999999999"
    FOLDER = "aaaaaaaa-0000-0000-0000-000000000001"

    def test_node_row_without_tree_group_is_skipped(self, write_ptir: WritePtir) -> None:
        path = write_ptir("OPTIRSpectrum", np.zeros(3, np.float32))
        with h5py.File(path, "a") as h5:
            tree = h5.create_group("TREE")
            tree.create_dataset("NODES", data=_guid_rows(self.LEAF, self.MISSING))
            tree.create_group(self.LEAF).attrs["TYPE"] = np.bytes_(b"OPTIRSpectrum")
        with ptir5.open(path) as f:
            assert f.tree is not None
            assert [leaf.guid for leaf in f.tree.leaves] == [self.LEAF]

    def test_folder_cycle_is_cut(self, write_ptir: WritePtir) -> None:
        path = write_ptir("OPTIRSpectrum", np.zeros(3, np.float32))
        with h5py.File(path, "a") as h5:
            tree = h5.create_group("TREE")
            tree.create_dataset("NODES", data=_guid_rows(self.FOLDER))
            folder = tree.create_group(self.FOLDER)
            folder.attrs["TYPE"] = np.bytes_(b"FOLDER")
            folder.attrs["Label"] = np.bytes_(b"Loop")
            folder.create_dataset("NODES", data=_guid_rows(self.FOLDER, self.LEAF))
            tree.create_group(self.LEAF).attrs["TYPE"] = np.bytes_(b"OPTIRSpectrum")
        with ptir5.open(path) as f:
            assert f.tree is not None
            (loop,) = f.tree.folders
            assert loop.folders == ()
            assert [leaf.guid for leaf in loop.leaves] == [self.LEAF]
