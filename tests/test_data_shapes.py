"""Tests for numpy array shapes and dtypes per measurement type."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

import ptir5
from ptir5 import DataShape

if TYPE_CHECKING:
    from pathlib import Path


class TestFloatSpectrum1D:
    def test_optir_spectrum_shape(self, optir_spectrum_path: Path) -> None:
        with ptir5.open(optir_spectrum_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FloatSpectrum1D)
            assert m.data_shape == DataShape.FLOAT_SPECTRUM_1D
            data = m.data
            assert data.ndim == 1
            assert data.dtype == np.float32
            assert data.shape == (1019,)

    def test_optir_spectrum_properties(self, optir_spectrum_path: Path) -> None:
        with ptir5.open(optir_spectrum_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRSpectrum)
            assert m.num_points == 1019
            assert m.x_start == 962.0
            assert m.x_increment == 2.0
            x = m.x_values
            assert len(x) == 1019
            assert x[0] == 962.0
            assert x[1] == 964.0

    def test_raman_spectrum_shape(self, raman_spectrum_path: Path) -> None:
        with ptir5.open(raman_spectrum_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.RamanSpectrum)
            data = m.data
            assert data.shape == (1024,)
            assert data.dtype == np.float32


class TestFloatImage2D:
    def test_optir_image_shape(self, optir_image_path: Path) -> None:
        with ptir5.open(optir_image_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FloatImage2D)
            assert m.data_shape == DataShape.FLOAT_IMAGE_2D
            data = m.data
            assert data.ndim == 2
            assert data.dtype == np.float32
            assert data.shape == (501, 501)

    def test_optir_image_properties(self, optir_image_path: Path) -> None:
        with ptir5.open(optir_image_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRImage)
            assert m.pixel_height == 501
            assert m.pixel_width == 501
            assert m.image_width_um == 50.0
            assert m.image_height_um == 50.0


class TestByteImage2D:
    def test_camera_image_shape(self, camera_image_path: Path) -> None:
        with ptir5.open(camera_image_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.ByteImage2D)
            assert m.data_shape == DataShape.BYTE_IMAGE_2D
            data = m.data
            assert data.ndim == 3
            assert data.dtype == np.uint8
            assert data.shape == (300, 400, 4)

    def test_camera_image_properties(self, camera_image_path: Path) -> None:
        with ptir5.open(camera_image_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.CameraImage)
            assert m.pixel_height == 300
            assert m.pixel_width == 400
            assert m.bytes_per_pixel == 4
            assert m.pixel_format == ptir5.PixelFormat.Bgra32

    def test_flptir_image_shape(self, flptir_image_path: Path) -> None:
        with ptir5.open(flptir_image_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImage)
            data = m.data
            assert data.shape == (256, 256, 4)
            assert data.dtype == np.uint8


class TestFloatHypercube3D:
    def test_hyperspectra_shape(self, hyperspectra_path: Path) -> None:
        with ptir5.open(hyperspectra_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FloatHypercube3D)
            assert m.data_shape == DataShape.FLOAT_HYPERCUBE_3D
            data = m.data
            assert data.ndim == 3
            assert data.dtype == np.float32
            assert data.shape == (574, 20, 20)

    def test_hyperspectra_properties(self, hyperspectra_path: Path) -> None:
        with ptir5.open(hyperspectra_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRHyperspectra)
            assert m.num_points == 574
            assert m.pixel_height == 20
            assert m.pixel_width == 20
            assert m.x_start == 749.5
            assert m.x_increment == 2.0
            x = m.x_values
            assert len(x) == 574

    def test_hyperspectra_read_spectrum(self, hyperspectra_path: Path) -> None:
        with ptir5.open(hyperspectra_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRHyperspectra)
            spec = m.read_spectrum(0, 0)
            assert spec.shape == (574,)

    def test_hyperspectra_read_image(self, hyperspectra_path: Path) -> None:
        with ptir5.open(hyperspectra_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRHyperspectra)
            img = m.read_image(0)
            assert img.shape == (20, 20)

    def test_optir_image_stack_shape(self, optir_image_stack_path: Path) -> None:
        with ptir5.open(optir_image_stack_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.OPTIRImageStack)
            assert m.data_shape == DataShape.FLOAT_HYPERCUBE_3D
            data = m.data
            assert data.shape == (19, 51, 51)
            assert data.dtype == np.float32


class TestByteImageStack3D:
    def test_flptir_stack_shape(self, flptir_stack_path: Path) -> None:
        with ptir5.open(flptir_stack_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.ByteImageStack3D)
            assert m.data_shape == DataShape.BYTE_IMAGE_STACK_3D
            data = m.data
            assert data.ndim == 4
            assert data.dtype == np.uint8
            assert data.shape == (5, 256, 256, 4)

    def test_flptir_stack_properties(self, flptir_stack_path: Path) -> None:
        with ptir5.open(flptir_stack_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)
            assert m.num_images == 5
            assert m.pixel_height == 256
            assert m.pixel_width == 256
            assert m.bytes_per_pixel == 4

    def test_flptir_stack_read_image(self, flptir_stack_path: Path) -> None:
        with ptir5.open(flptir_stack_path) as f:
            m = f.measurements[0]
            assert isinstance(m, ptir5.FLPTIRImageStack)
            img = m.read_image(0)
            assert img.shape == (256, 256, 4)
