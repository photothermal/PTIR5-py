"""Regression tests for previously identified edge cases."""

from __future__ import annotations

from typing import TYPE_CHECKING

import h5py
import numpy as np
import pytest

import ptir5

if TYPE_CHECKING:
    from pathlib import Path


def _write_minimal_file(path: Path) -> None:
    with h5py.File(path, "w") as h5:
        h5.create_group("MEASUREMENTS")
        h5.create_group("BACKGROUNDS")


def test_scalar_string_arrays_decode_cleanly(tmp_path: Path) -> None:
    file_path = tmp_path / "scalar_string_arrays.ptir"
    _write_minimal_file(file_path)

    with h5py.File(file_path, "a") as h5:
        g = h5["MEASUREMENTS"].create_group("12345678-1234-1234-1234-1234567890ab")
        g.attrs["TYPE"] = np.array([np.bytes_(b"OPTIRSpectrum")])
        g.attrs["Label"] = np.array([np.bytes_(b"Array Label")])
        g.create_dataset("DATA", data=np.zeros((8,), dtype=np.float32))

    with ptir5.open(file_path) as f:
        m = f.measurements[0]
        assert isinstance(m, ptir5.OPTIRSpectrum)
        assert m.label == "Array Label"


def test_measurement_data_after_close_raises_file_closed(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]

    with pytest.raises(ptir5.FileClosedError):
        _ = m.data


def test_unknown_type_uses_base_measurement_class(tmp_path: Path) -> None:
    file_path = tmp_path / "unknown_type.ptir"
    _write_minimal_file(file_path)

    with h5py.File(file_path, "a") as h5:
        g = h5["MEASUREMENTS"].create_group("87654321-4321-4321-4321-ba0987654321")
        g.attrs["TYPE"] = np.bytes_(b"UnknownType2DUInt8")
        g.create_dataset("DATA", data=np.zeros((5, 6), dtype=np.uint8))

    with ptir5.open(file_path) as f:
        m = f.measurements[0]
        assert type(m) is ptir5.Measurement
        assert m.measurement_type == "UnknownType2DUInt8"
        assert m.data.shape == (5, 6)
