"""FLPTIR image stack — dual-format (legacy rank-4 byte / new rank-3 float) tests.

Mirrors the C# PSC.PTIR5.SDK ``FLPTIRImageStack`` dual-format support: a stack
may be stored either as ``(N, H, W, 4) uint8`` (legacy, with each 4-byte pixel
being a float32 value) or as ``(N, H, W) float32`` (new format). Callers should
see the same float32 imagery either way.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import h5py
import numpy as np
import pytest

import ptir5
from ptir5 import DataShape

if TYPE_CHECKING:
    from pathlib import Path


def _write_stack_file(
    path: Path,
    data: np.ndarray,
    guid: str = "11111111-2222-3333-4444-555555555555",
) -> None:
    """Write a minimal PTIR5 file with a single FLPTIRImageStack measurement."""
    with h5py.File(path, "w") as h5:
        h5.create_group("BACKGROUNDS")
        measurements = h5.create_group("MEASUREMENTS")
        g = measurements.create_group(guid)
        g.attrs["TYPE"] = np.bytes_(b"FLPTIRImageStack")
        g.attrs["Label"] = np.bytes_(b"Test Stack")
        g.create_dataset("DATA", data=data)


class TestRank3FloatFormat:
    """New rank-3 float32 storage — the format PTIR Studio writes for newly
    allocated FLPTIR stacks (matches C# FLPTIRImageStack.Allocate)."""

    def test_shape_and_dtype(self, tmp_path: Path) -> None:
        expected = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
        _write_stack_file(tmp_path / "rank3.ptir", expected)

        with ptir5.open(tmp_path / "rank3.ptir") as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)
            assert m.is_legacy is False
            assert m.data_shape == DataShape.FLOAT_IMAGE_STACK_3D
            assert m.num_images == 2
            assert m.pixel_height == 3
            assert m.pixel_width == 4

            np.testing.assert_array_equal(m.data, expected)
            np.testing.assert_array_equal(m.data_float32, expected)

    def test_read_image_returns_2d_float32(self, tmp_path: Path) -> None:
        expected = np.array(
            [
                [[1.5, 2.5], [3.5, 4.5]],
                [[10.5, 20.5], [30.5, 40.5]],
                [[100.5, 200.5], [300.5, 400.5]],
            ],
            dtype=np.float32,
        )
        _write_stack_file(tmp_path / "rank3.ptir", expected)

        with ptir5.open(tmp_path / "rank3.ptir") as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)

            img0 = m.read_image(0)
            assert img0.shape == (2, 2)
            assert img0.dtype == np.float32
            np.testing.assert_array_equal(img0, expected[0])

            img2 = m.read_image(2)
            np.testing.assert_array_equal(img2, expected[2])

    def test_bytes_per_pixel_undefined_for_float_format(self, tmp_path: Path) -> None:
        """Rank-3 float stacks are FloatImageStack3D, not ByteImageStack3D, so
        ``bytes_per_pixel`` (a byte-storage concept) is not defined on them."""
        _write_stack_file(
            tmp_path / "rank3.ptir",
            np.zeros((1, 2, 2), dtype=np.float32),
        )

        with ptir5.open(tmp_path / "rank3.ptir") as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)
            assert isinstance(m, ptir5.FloatImageStack3D)
            assert not isinstance(m, ptir5.ByteImageStack3D)

            with pytest.raises(AttributeError, match="bytes_per_pixel"):
                _ = m.bytes_per_pixel  # type: ignore[attr-defined]


class TestRank4LegacyByteFormat:
    """Legacy rank-4 byte storage — each 4-byte pixel is the byte representation
    of a float32 value (matches C# FLPTIRImageStack legacy ReadImagef path)."""

    def test_byte_reinterpret_round_trips_float32(self, tmp_path: Path) -> None:
        """Write known float32 values as their 4-byte representation, then read
        back via the legacy rank-4 path. The reinterpret cast must recover the
        original float32 values exactly."""
        # Pick distinct non-trivial float values including negatives, fractions,
        # and a NaN to confirm bit-exact reinterpret (not a numeric conversion).
        floats = np.array(
            [
                [[1.5, -2.25], [3.125, np.nan]],
                [[10.5, 0.0], [-100.0, 1e-30]],
            ],
            dtype=np.float32,
        )
        # Reshape into the legacy on-disk layout (N, H, W, 4) of raw bytes.
        as_bytes = floats.view(np.uint8).reshape(floats.shape + (4,))
        _write_stack_file(tmp_path / "rank4.ptir", as_bytes)

        with ptir5.open(tmp_path / "rank4.ptir") as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)
            assert m.is_legacy is True
            assert m.data_shape == DataShape.BYTE_IMAGE_STACK_3D
            assert m.bytes_per_pixel == 4
            assert m.num_images == 2
            assert m.pixel_height == 2
            assert m.pixel_width == 2

            # data_float32 recovers the original values bit-exact.
            recovered = m.data_float32
            assert recovered.shape == (2, 2, 2)
            assert recovered.dtype == np.float32
            # Use bit-equality so NaN positions match regardless of payload.
            np.testing.assert_array_equal(
                recovered.view(np.uint32), floats.view(np.uint32)
            )

    def test_read_image_reinterprets_per_frame(self, tmp_path: Path) -> None:
        floats = np.array(
            [
                [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                [[7.0, 8.0, 9.0], [10.0, 11.0, 12.0]],
            ],
            dtype=np.float32,
        )
        as_bytes = floats.view(np.uint8).reshape(floats.shape + (4,))
        _write_stack_file(tmp_path / "rank4.ptir", as_bytes)

        with ptir5.open(tmp_path / "rank4.ptir") as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)

            img0 = m.read_image(0)
            assert img0.shape == (2, 3)
            assert img0.dtype == np.float32
            np.testing.assert_array_equal(img0, floats[0])

            img1 = m.read_image(1)
            np.testing.assert_array_equal(img1, floats[1])

    def test_legacy_isinstance_dispatch(self, tmp_path: Path) -> None:
        """Legacy FLPTIR stacks satisfy both the storage-shape contract
        (ByteImageStack3D, ImageStack3D) and the measurement-type contract
        (FLPTIRImageStack)."""
        floats = np.array([[[1.0, 2.0]]], dtype=np.float32)
        as_bytes = floats.view(np.uint8).reshape(1, 1, 2, 4)
        _write_stack_file(tmp_path / "rank4.ptir", as_bytes)

        with ptir5.open(tmp_path / "rank4.ptir") as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)
            assert isinstance(m, ptir5.ByteImageStack3D)
            assert isinstance(m, ptir5.ImageStack3D)
            assert not isinstance(m, ptir5.FloatImageStack3D)

    def test_rank4_validation_rejects_wrong_dtype(self, tmp_path: Path) -> None:
        """A rank-4 FLPTIRImageStack DATA dataset with non-uint8 dtype is
        malformed; reading via the float32 paths must raise
        InvalidMeasurementError rather than silently producing garbage or
        leaking a raw numpy ValueError."""
        bogus = np.zeros((2, 3, 4, 4), dtype=np.int32)
        _write_stack_file(tmp_path / "bad_dtype.ptir", bogus)

        with ptir5.open(tmp_path / "bad_dtype.ptir") as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)
            assert isinstance(m, ptir5.ByteImageStack3D)

            with pytest.raises(ptir5.InvalidMeasurementError, match="uint8"):
                _ = m.data_float32

            with pytest.raises(ptir5.InvalidMeasurementError, match="uint8"):
                _ = m.read_image(0)

    def test_rank4_validation_rejects_wrong_trailing_dim(self, tmp_path: Path) -> None:
        """Rank-4 uint8 with trailing dim != 4 is malformed."""
        bogus = np.zeros((2, 3, 4, 2), dtype=np.uint8)
        _write_stack_file(tmp_path / "bad_trailing.ptir", bogus)

        with ptir5.open(tmp_path / "bad_trailing.ptir") as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)

            with pytest.raises(ptir5.InvalidMeasurementError, match="trailing dim 4"):
                _ = m.data_float32

            with pytest.raises(ptir5.InvalidMeasurementError, match="trailing dim 4"):
                _ = m.read_image(0)

    def test_raw_data_still_accessible_as_bytes(self, tmp_path: Path) -> None:
        """The ``data`` property remains the unmodified on-disk dataset; this
        keeps the legacy raw-byte access path working for callers who need it."""
        floats = np.array([[[1.0, 2.0]]], dtype=np.float32)  # (1, 1, 2)
        as_bytes = floats.view(np.uint8).reshape(1, 1, 2, 4)
        _write_stack_file(tmp_path / "rank4.ptir", as_bytes)

        with ptir5.open(tmp_path / "rank4.ptir") as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)

            raw = m.data
            assert raw.dtype == np.uint8
            assert raw.shape == (1, 1, 2, 4)
            np.testing.assert_array_equal(raw, as_bytes)
