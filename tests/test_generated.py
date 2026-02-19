"""Tests for GENERATED sub-items of hyperspectral and stack measurements."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

import ptir5

if TYPE_CHECKING:
    from pathlib import Path


def test_hyperspectra_generated_items(hyperspectra_path: Path) -> None:
    with ptir5.open(hyperspectra_path) as f:
        m = f.measurements[0]
        assert isinstance(m, ptir5.OPTIRHyperspectra)
        assert len(m.generated) == 2


def test_hyperspectra_generated_image(hyperspectra_path: Path) -> None:
    with ptir5.open(hyperspectra_path) as f:
        m = f.measurements[0]
        gen_images = [g for g in m.generated if isinstance(g, ptir5.GeneratedImage)]
        assert len(gen_images) == 1
        gi = gen_images[0]
        assert gi.measurement_type == ptir5.MeasurementType.GeneratedImage
        assert gi.data.shape == (20, 20)
        assert gi.data.dtype == np.float32


def test_hyperspectra_generated_spectrum(hyperspectra_path: Path) -> None:
    with ptir5.open(hyperspectra_path) as f:
        m = f.measurements[0]
        gen_spectra = [g for g in m.generated if isinstance(g, ptir5.GeneratedSpectrum)]
        assert len(gen_spectra) == 1
        gs = gen_spectra[0]
        assert gs.measurement_type == ptir5.MeasurementType.GeneratedSpectrum
        assert gs.data.shape == (574,)
        assert gs.data.dtype == np.float32
        assert gs.label == "ROI Spectrum 1"


def test_generated_spectrum_metadata(hyperspectra_path: Path) -> None:
    with ptir5.open(hyperspectra_path) as f:
        m = f.measurements[0]
        gen_spectra = [g for g in m.generated if isinstance(g, ptir5.GeneratedSpectrum)]
        gs = gen_spectra[0]
        assert "XStart" in gs.metadata
        assert "XIncrement" in gs.metadata
        # ROIData sub-group
        assert "ROIData.ROIType" in gs.metadata
        assert gs.metadata["ROIData.ROIType"] == "POINT"


def test_generated_image_roi_metadata(hyperspectra_path: Path) -> None:
    with ptir5.open(hyperspectra_path) as f:
        m = f.measurements[0]
        gen_images = [g for g in m.generated if isinstance(g, ptir5.GeneratedImage)]
        gi = gen_images[0]
        assert "ROIData.ROIType" in gi.metadata
        assert "ROIData.ROIWidth" in gi.metadata


def test_optir_image_stack_generated(optir_image_stack_path: Path) -> None:
    with ptir5.open(optir_image_stack_path) as f:
        for m in f.measurements:
            assert len(m.generated) == 1
            gs = m.generated[0]
            assert isinstance(gs, ptir5.GeneratedSpectrum)
            assert gs.data.shape == (19,)


def test_flptir_stack_no_generated(flptir_stack_path: Path) -> None:
    """FLPTIR stack has an empty GENERATED group."""
    with ptir5.open(flptir_stack_path) as f:
        m = f.measurements[0]
        assert len(m.generated) == 0


def test_generated_has_guid(hyperspectra_path: Path) -> None:
    with ptir5.open(hyperspectra_path) as f:
        m = f.measurements[0]
        for g in m.generated:
            assert len(g.guid) > 0
