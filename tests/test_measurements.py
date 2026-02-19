"""Tests for flat measurement enumeration and lookup."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import ptir5
from ptir5 import MeasurementNotFoundError, MeasurementType

if TYPE_CHECKING:
    from pathlib import Path


def test_optir_spectrum_measurement(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        assert len(f.measurements) == 1
        m = f.measurements[0]
        assert m.measurement_type == MeasurementType.OPTIRSpectrum
        assert isinstance(m, ptir5.OPTIRSpectrum)
        assert m.label == "O-PTIR0 1"


def test_raman_spectrum_measurement(raman_spectrum_path: Path) -> None:
    with ptir5.open(raman_spectrum_path) as f:
        assert len(f.measurements) == 1
        m = f.measurements[0]
        assert m.measurement_type == MeasurementType.RamanSpectrum
        assert isinstance(m, ptir5.RamanSpectrum)
        assert m.label == "Spectrum 1"


def test_camera_image_measurement(camera_image_path: Path) -> None:
    with ptir5.open(camera_image_path) as f:
        assert len(f.measurements) == 1
        m = f.measurements[0]
        assert m.measurement_type == MeasurementType.CameraImage
        assert isinstance(m, ptir5.CameraImage)
        assert m.label == "Camera 1"


def test_optir_image_measurement(optir_image_path: Path) -> None:
    with ptir5.open(optir_image_path) as f:
        assert len(f.measurements) == 1
        m = f.measurements[0]
        assert m.measurement_type == MeasurementType.OPTIRImage
        assert isinstance(m, ptir5.OPTIRImage)


def test_flptir_image_measurement(flptir_image_path: Path) -> None:
    with ptir5.open(flptir_image_path) as f:
        assert len(f.measurements) == 1
        m = f.measurements[0]
        assert m.measurement_type == MeasurementType.FLPTIRImage
        assert isinstance(m, ptir5.FLPTIRImage)


def test_flptir_stack_measurement(flptir_stack_path: Path) -> None:
    with ptir5.open(flptir_stack_path) as f:
        assert len(f.measurements) == 1
        m = f.measurements[0]
        assert m.measurement_type == MeasurementType.FLPTIRImageStack
        assert isinstance(m, ptir5.FLPTIRImageStack)


def test_hyperspectra_measurement(hyperspectra_path: Path) -> None:
    with ptir5.open(hyperspectra_path) as f:
        assert len(f.measurements) == 1
        m = f.measurements[0]
        assert m.measurement_type == MeasurementType.OPTIRHyperspectra
        assert isinstance(m, ptir5.OPTIRHyperspectra)


def test_optir_image_stack_measurements(optir_image_stack_path: Path) -> None:
    with ptir5.open(optir_image_stack_path) as f:
        assert len(f.measurements) == 2
        for m in f.measurements:
            assert m.measurement_type == MeasurementType.OPTIRImageStack
            assert isinstance(m, ptir5.OPTIRImageStack)


def test_get_measurement_by_guid(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        found = f.get_measurement(m.guid)
        assert found is m


def test_get_measurement_not_found(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f, pytest.raises(MeasurementNotFoundError):
        f.get_measurement("nonexistent-guid")


def test_measurements_by_type(optir_image_stack_path: Path) -> None:
    with ptir5.open(optir_image_stack_path) as f:
        stacks = f.measurements_by_type(MeasurementType.OPTIRImageStack)
        assert len(stacks) == 2
        spectra = f.measurements_by_type(MeasurementType.OPTIRSpectrum)
        assert len(spectra) == 0


def test_measurements_cached(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m1 = f.measurements
        m2 = f.measurements
        assert m1 is m2
