"""Time-domain measurement types (PSC.PTIR5.SDK TimeDomainBurst / TimeDomainCube).

A burst is a spectrum-shaped waveform with a time axis (µs); a cube is the
hyperspectral-shaped array analog, one burst per X/Y location.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

import ptir5
from ptir5 import DataShape, MeasurementType

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    WritePtir = Callable[..., Path]


def test_time_domain_burst_is_a_typed_spectrum(write_ptir: WritePtir) -> None:
    data = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    path = write_ptir("TimeDomainBurst", data, attrs={
        "XStart": np.float32(2.0), "XIncrement": np.float32(0.5), "XUnits": "µs",
        "SampleRate": np.float64(2.0e6), "BurstBackend": "M5i", "BurstOverflow": np.uint8(0),
    })
    with ptir5.open(path) as f:
        m = f.measurements[0]
        assert isinstance(m, ptir5.TimeDomainBurst)
        assert isinstance(m, ptir5.FloatSpectrum1D)
        assert m.measurement_type is MeasurementType.TimeDomainBurst
        assert m.data_shape == DataShape.FLOAT_SPECTRUM_1D
        np.testing.assert_array_equal(m.data, data)
        np.testing.assert_allclose(m.x_values, [2.0, 2.5, 3.0, 3.5])
        assert m.metadata["XUnits"] == "µs"
        assert m.metadata["SampleRate"] == 2.0e6
        assert m.metadata["BurstBackend"] == "M5i"
        assert f.measurements_by_type(MeasurementType.TimeDomainBurst) == (m,)


def test_time_domain_cube_is_a_hyperspectral_cube(write_ptir: WritePtir) -> None:
    data = np.arange(4 * 2 * 3, dtype=np.float32).reshape(4, 2, 3)
    path = write_ptir(
        "TimeDomainCube", data,
        attrs={"XStart": np.float32(0.0), "XIncrement": np.float32(0.5), "XUnits": "µs"},
        generated=[("GeneratedImage", np.zeros((2, 3), np.float32), {})],
    )
    with ptir5.open(path) as f:
        m = f.measurements[0]
        assert isinstance(m, ptir5.TimeDomainCube)
        assert isinstance(m, ptir5.HyperspectralCube)
        assert m.measurement_type is MeasurementType.TimeDomainCube
        assert m.data_shape == DataShape.FLOAT_HYPERCUBE_3D
        assert (m.num_points, m.pixel_height, m.pixel_width) == (4, 2, 3)
        np.testing.assert_array_equal(m.read_spectrum(x=2, y=1), data[:, 1, 2])
        np.testing.assert_array_equal(m.read_image(3), data[3])
        assert [type(g) for g in m.generated] == [ptir5.GeneratedImage]


def test_only_spectral_and_time_cubes_share_the_hyperspectral_base(
    write_ptir: WritePtir, hyperspectra_path: Path, optir_image_stack_path: Path
) -> None:
    with ptir5.open(hyperspectra_path) as f:
        assert isinstance(f.measurements[0], ptir5.HyperspectralCube)
    with ptir5.open(write_ptir("RamanHyperspectra", np.zeros((2, 1, 1), np.float32))) as f:
        assert isinstance(f.measurements[0], ptir5.HyperspectralCube)
    with ptir5.open(optir_image_stack_path) as f:
        assert not isinstance(f.measurements[0], ptir5.HyperspectralCube)
