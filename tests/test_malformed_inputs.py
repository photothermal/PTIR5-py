"""Tests for malformed HDF5 input handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

import h5py
import numpy as np
import pytest

import ptir5
from ptir5 import InvalidMeasurementError

if TYPE_CHECKING:
    from pathlib import Path


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
