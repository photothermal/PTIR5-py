"""Normalization *settings* for hyperspectral cubes and band images (spec §13.4).

ptir5 reports the setting PTIR Studio would render with; it never normalizes
the stored samples. Rules mirror PSC.PTIR5.SDK ``HyperspectralArrayData`` and
``GeneratedImage``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

import ptir5
from ptir5 import NormalizeMode, NormalizeSpec

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    WritePtir = Callable[..., Path]

CUBE = np.zeros((4, 2, 3), dtype=np.float32)
BAND = np.zeros((2, 3), dtype=np.float32)
CUBE_WN = {"NormalizeMode": "Wavenumber", "NormalizeWavenumber": np.float32(1650.0)}
Off, Peak, Wn, Time, Offset = (NormalizeMode.Off, NormalizeMode.Peak, NormalizeMode.Wavenumber,
                               NormalizeMode.Time, NormalizeMode.Offset)


def test_untracked_cube_is_off(hyperspectra_path: Path) -> None:
    with ptir5.open(hyperspectra_path) as f:
        assert f.measurements[0].normalize_spec == NormalizeSpec(Off, None)
        assert f.measurements[0].resolve_normalize_spec() == NormalizeSpec(Off, None)


def test_supported_modes_follow_the_cube_axis() -> None:
    assert ptir5.OPTIRHyperspectra.supported_normalize_modes == {Off, Peak, Wn}
    assert ptir5.RamanHyperspectra.supported_normalize_modes == {Off, Peak, Wn}
    assert ptir5.TimeDomainCube.supported_normalize_modes == {Off, Peak, Time, Offset}


@pytest.mark.parametrize(("type_", "stored", "expected"), [
    ("OPTIRHyperspectra", "Wavenumber", Wn), ("OPTIRHyperspectra", "wavenumber", Wn),
    ("OPTIRHyperspectra", "Peak", Peak), ("RamanHyperspectra", "Wavenumber", Wn),
    ("OPTIRHyperspectra", "Time", Off), ("OPTIRHyperspectra", "Offset", Off),
    ("OPTIRHyperspectra", "Bogus", Off), ("OPTIRHyperspectra", "Off", Off),
    ("TimeDomainCube", "Offset", Offset), ("TimeDomainCube", "Time", Time),
    ("TimeDomainCube", "Peak", Peak), ("TimeDomainCube", "Wavenumber", Off),
])
def test_cube_mode_resolution(
    write_ptir: WritePtir, type_: str, stored: str, expected: NormalizeMode
) -> None:
    path = write_ptir(type_, CUBE, attrs={"NormalizeMode": stored,
                                          "NormalizeWavenumber": np.float32(1650.0)})
    with ptir5.open(path) as f:
        assert f.measurements[0].normalize_spec == NormalizeSpec(expected, 1650.0)


def test_axis_mode_without_reference_keeps_none(write_ptir: WritePtir) -> None:
    path = write_ptir("OPTIRHyperspectra", CUBE, attrs={"NormalizeMode": "Wavenumber"})
    with ptir5.open(path) as f:
        assert f.measurements[0].normalize_spec == NormalizeSpec(Wn, None)


@pytest.mark.parametrize(("cube_type", "image_attrs", "own", "effective"), [
    # Absent: follow the cube.
    ("OPTIRHyperspectra", {}, None, NormalizeSpec(Wn, 1650.0)),
    # Explicit Off is distinct from absent.
    ("OPTIRHyperspectra", {"NormalizeMode": "Off"},
     NormalizeSpec(Off, None), NormalizeSpec(Off, None)),
    # An own mode never borrows the cube's reference.
    ("OPTIRHyperspectra", {"NormalizeMode": "Wavenumber"},
     NormalizeSpec(Wn, None), NormalizeSpec(Wn, None)),
    ("OPTIRHyperspectra", {"NormalizeMode": "Peak", "NormalizeWavenumber": np.float32(1200.0)},
     NormalizeSpec(Peak, 1200.0), NormalizeSpec(Peak, 1200.0)),
    # Unparseable reads Off, not absent.
    ("OPTIRHyperspectra", {"NormalizeMode": "Garbage"},
     NormalizeSpec(Off, None), NormalizeSpec(Off, None)),
    # A mode the parent cube type does not support reads Off.
    ("TimeDomainCube", {"NormalizeMode": "Wavenumber", "NormalizeWavenumber": np.float32(3.0)},
     NormalizeSpec(Wn, 3.0), NormalizeSpec(Off, 3.0)),
])
def test_band_image_resolution(
    write_ptir: WritePtir, cube_type: str, image_attrs: dict[str, object],
    own: NormalizeSpec | None, effective: NormalizeSpec,
) -> None:
    path = write_ptir(cube_type, CUBE, attrs=CUBE_WN,
                      generated=[("GeneratedImage", BAND, image_attrs)])
    with ptir5.open(path) as f:
        cube = f.measurements[0]
        image = cube.generated[0]
        assert image.normalize_spec == own
        assert cube.resolve_normalize_spec(image) == effective
