"""FLPTIR image — dual-format (rank-2 canonical / legacy rank-3 byte) tests.

Mirrors the C# PSC.PTIR5.SDK ``FLPTIRImage`` reader: current files store
``(H, W)`` float32, uint16 or uint8 (the dtype decides the pixel format), and
legacy Gray32Float files store ``(H, W, 4) uint8`` where each 4-byte pixel is a
float32 value. Callers see the same float32 imagery either way.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

import ptir5
from ptir5 import DataShape, InvalidMeasurementError, PixelFormat

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    WritePtir = Callable[..., Path]


def test_legacy_rank3_image_reads_as_float32(flptir_image_path: Path) -> None:
    with ptir5.open(flptir_image_path) as f:
        m = f.measurements[0]
        assert isinstance(m, ptir5.FLPTIRImage) and isinstance(m, ptir5.ByteImage2D)
        assert m.is_legacy is True
        assert m.data_shape == DataShape.BYTE_IMAGE_2D
        raw = m.data
        assert raw.shape == (256, 256, 4) and raw.dtype == np.uint8
        image = m.data_float32
        assert image.shape == (256, 256) and image.dtype == np.float32
        np.testing.assert_array_equal(image, raw.view(np.float32).reshape(256, 256))


@pytest.mark.parametrize(("dtype", "pixel_format"), [
    (np.float32, PixelFormat.Gray32Float), (np.uint16, PixelFormat.Gray16),
    (np.uint8, PixelFormat.Gray8),
])
def test_rank2_image_reads_as_float32(
    write_ptir: WritePtir, dtype: type, pixel_format: PixelFormat
) -> None:
    stored = np.array([[1, 2, 3], [4, 5, 250]], dtype=dtype)
    path = write_ptir("FLPTIRImage", stored, attrs={"PixelFormat": pixel_format.name})
    with ptir5.open(path) as f:
        m = f.measurements[0]
        assert isinstance(m, ptir5.FLPTIRImage) and isinstance(m, ptir5.FloatImage2D)
        assert not isinstance(m, ptir5.ByteImage2D)
        assert m.is_legacy is False
        assert m.data_shape == DataShape.FLOAT_IMAGE_2D
        assert (m.pixel_height, m.pixel_width) == (2, 3)
        assert m.pixel_format is pixel_format
        assert m.data.dtype == dtype
        assert m.data_float32.dtype == np.float32
        np.testing.assert_array_equal(m.data_float32, stored.astype(np.float32))


@pytest.mark.parametrize("data", [
    np.zeros((2, 3), np.float64), np.zeros((2, 3), np.int32),
    np.zeros((3,), np.float32), np.zeros((1, 2, 3, 4), np.uint8), None,
])
def test_unsupported_layouts_raise_on_open(write_ptir: WritePtir, data: np.ndarray | None) -> None:
    with ptir5.open(write_ptir("FLPTIRImage", data)) as f, pytest.raises(InvalidMeasurementError):
        _ = f.measurements


def test_malformed_legacy_bytes_raise_on_read(write_ptir: WritePtir) -> None:
    with ptir5.open(write_ptir("FLPTIRImage", np.zeros((2, 3, 3), np.uint8))) as f:
        m = f.measurements[0]
        with pytest.raises(InvalidMeasurementError):
            _ = m.data_float32


@pytest.mark.parametrize(("dtype", "stored", "expected"), [
    (np.float32, None, PixelFormat.Gray32Float),
    (np.uint16, None, PixelFormat.Gray16),
    (np.uint8, None, PixelFormat.Gray8),
    # As in the SDK, integer storage decides over a contradicting stored name.
    (np.uint16, "Gray8", PixelFormat.Gray16),
])
def test_rank2_pixel_format_follows_the_dtype(
    write_ptir: WritePtir, dtype: type, stored: str | None, expected: PixelFormat
) -> None:
    attrs = {} if stored is None else {"PixelFormat": stored}
    path = write_ptir("FLPTIRImage", np.zeros((2, 3), dtype=dtype), attrs=attrs)
    with ptir5.open(path) as f:
        assert f.measurements[0].pixel_format is expected
