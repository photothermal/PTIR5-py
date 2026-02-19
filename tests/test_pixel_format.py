"""Tests for PixelFormat enum resolution from integer and string values."""

from __future__ import annotations

from typing import TYPE_CHECKING

import h5py
import numpy as np

import ptir5
from ptir5 import PixelFormat

if TYPE_CHECKING:
    from pathlib import Path


class TestPixelFormatEnum:
    def test_all_named_values(self) -> None:
        """Every PixelFormat member should be accessible by name."""
        assert PixelFormat["Bgra32"] == PixelFormat.Bgra32
        assert PixelFormat["Rgb24"] == PixelFormat.Rgb24
        assert PixelFormat["Gray8"] == PixelFormat.Gray8

    def test_integer_values(self) -> None:
        """PixelFormat should resolve from integer values."""
        assert PixelFormat(15) == PixelFormat.Bgra32
        assert PixelFormat(13) == PixelFormat.Rgb24
        assert PixelFormat(8) == PixelFormat.Gray8
        assert PixelFormat(12) == PixelFormat.Bgr24
        assert PixelFormat(0) == PixelFormat.Default

    def test_unknown_integer_raises(self) -> None:
        """Non-existent integer value should raise ValueError."""
        import pytest

        with pytest.raises(ValueError, match="99"):
            PixelFormat(99)

    def test_pixel_format_from_fixture(self, camera_image_path: Path) -> None:
        """Camera image fixture should have Bgra32 pixel format."""
        with ptir5.open(camera_image_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.CameraImage)
            assert m.pixel_format == PixelFormat.Bgra32
            assert m.pixel_format == 15

    def test_pixel_format_unknown_string_fallback(self, tmp_path: Path) -> None:
        """Unknown PixelFormat string should fall back to raw string."""
        path = tmp_path / "unknown_pf.ptir"
        with h5py.File(path, "w") as h5:
            h5.create_group("MEASUREMENTS")
            h5.create_group("BACKGROUNDS")
            g = h5["MEASUREMENTS"].create_group("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
            g.attrs["TYPE"] = np.bytes_(b"CameraImage")
            g.attrs["PixelFormat"] = np.bytes_(b"FutureFormat99")
            g.create_dataset("DATA", data=np.zeros((2, 2, 3), dtype=np.uint8))

        with ptir5.open(path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.CameraImage)
            assert m.pixel_format == "FutureFormat99"

    def test_pixel_format_numeric_attribute(self, tmp_path: Path) -> None:
        """Integer PixelFormat attribute should fall back to string of the int."""
        path = tmp_path / "numeric_pf.ptir"
        with h5py.File(path, "w") as h5:
            h5.create_group("MEASUREMENTS")
            h5.create_group("BACKGROUNDS")
            g = h5["MEASUREMENTS"].create_group("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
            g.attrs["TYPE"] = np.bytes_(b"CameraImage")
            g.attrs["PixelFormat"] = 15  # numeric instead of string
            g.create_dataset("DATA", data=np.zeros((2, 2, 4), dtype=np.uint8))

        with ptir5.open(path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.CameraImage)
            # PixelFormat lookup uses name-based access (PixelFormat[raw]),
            # so an integer falls back to the string representation
            pf = m.pixel_format
            assert isinstance(pf, str)
