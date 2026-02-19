"""Tests for background spectra access."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

import ptir5

if TYPE_CHECKING:
    from pathlib import Path


def test_camera_image_has_background(camera_image_path: Path) -> None:
    with ptir5.open(camera_image_path) as f:
        assert len(f.backgrounds) == 1
        bg = f.backgrounds[0]
        assert isinstance(bg, ptir5.FloatSpectrum1D)
        assert bg.data.ndim == 1
        assert bg.data.dtype == np.float32


def test_raman_spectrum_has_background(raman_spectrum_path: Path) -> None:
    with ptir5.open(raman_spectrum_path) as f:
        assert len(f.backgrounds) == 1
        bg = f.backgrounds[0]
        assert bg.data.shape == (549,)
        assert bg.label == "Spectrum 2"


def test_optir_spectrum_no_backgrounds(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        assert len(f.backgrounds) == 0


def test_get_background_by_guid(camera_image_path: Path) -> None:
    with ptir5.open(camera_image_path) as f:
        bg = f.backgrounds[0]
        found = f.get_background(bg.guid)
        assert found is bg


def test_get_background_not_found(camera_image_path: Path) -> None:
    import pytest

    with ptir5.open(camera_image_path) as f, pytest.raises(ptir5.MeasurementNotFoundError):
        f.get_background("nonexistent-guid")


def test_backgrounds_cached(raman_spectrum_path: Path) -> None:
    with ptir5.open(raman_spectrum_path) as f:
        b1 = f.backgrounds
        b2 = f.backgrounds
        assert b1 is b2
