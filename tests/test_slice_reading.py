"""Tests verifying slice-based reading doesn't load full arrays."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import numpy as np

import ptir5
from ptir5._reader import HDF5Reader

if TYPE_CHECKING:
    from pathlib import Path


class TestSliceBasedReading:
    def test_read_spectrum_uses_slice(self, hyperspectra_path: Path) -> None:
        """read_spectrum should return correct data via slice read."""
        with ptir5.open(hyperspectra_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRHyperspectra)

            # Read via slice method
            spec = m.read_spectrum(0, 0)
            assert spec.shape == (574,)
            assert spec.dtype == np.float32

            # Verify it matches full array indexing
            full = m.data
            np.testing.assert_array_equal(spec, full[:, 0, 0])

    def test_read_image_uses_slice(self, hyperspectra_path: Path) -> None:
        """read_image should return correct data via slice read."""
        with ptir5.open(hyperspectra_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRHyperspectra)

            img = m.read_image(0)
            assert img.shape == (20, 20)
            assert img.dtype == np.float32

            full = m.data
            np.testing.assert_array_equal(img, full[0, :, :])

    def test_byte_stack_read_image_uses_slice(self, flptir_stack_path: Path) -> None:
        """ByteImageStack3D.read_image should return correct data via slice read."""
        with ptir5.open(flptir_stack_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)

            img = m.read_image(0)
            assert img.shape == (256, 256, 4)
            assert img.dtype == np.uint8

            full = m.data
            np.testing.assert_array_equal(img, full[0, :, :, :])

    def test_slice_does_not_call_read_dataset(self, hyperspectra_path: Path) -> None:
        """Slice helpers should call read_dataset_slice, not read_dataset."""
        with ptir5.open(hyperspectra_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRHyperspectra)

            with patch.object(
                HDF5Reader, "read_dataset", wraps=m._reader.read_dataset
            ) as mock:
                _ = m.read_spectrum(0, 0)
                _ = m.read_image(0)
                mock.assert_not_called()

    def test_read_dataset_slice_method(self, hyperspectra_path: Path) -> None:
        """read_dataset_slice should work directly on the reader."""
        with ptir5.open(hyperspectra_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRHyperspectra)

            data_path = f"{m._hdf5_path}/DATA"
            sliced = m._reader.read_dataset_slice(data_path, (0, slice(None), slice(None)))
            assert sliced.shape == (20, 20)

            full = m._reader.read_dataset(data_path)
            np.testing.assert_array_equal(sliced, full[0, :, :])
