"""Side datasets stored next to DATA, and opt-in component-completion tracking.

Spec §4.3 places per-pixel and per-image auxiliary arrays beside ``DATA``;
§7.4.1 defines ``ComponentCompletion`` (absent = unknown, 1 = complete, any
other value = incomplete, fail closed).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

import ptir5
from ptir5 import FileClosedError, InvalidMeasurementError

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    WritePtir = Callable[..., Path]

STACK_SIDE_DATASETS = {
    "BalDetSum", "BalDetVoltage", "BottomFocus", "DcValue", "Humidity", "MaxValue",
    "MinValue", "NumAverages", "Temperature", "TopFocus", "Wavenumber",
}


def test_stack_side_datasets_exclude_data_and_groups(optir_image_stack_path: Path) -> None:
    with ptir5.open(optir_image_stack_path) as f:
        aux = f.measurements[0].auxiliary
        assert set(aux) == STACK_SIDE_DATASETS          # not DATA, Channel or GENERATED
        assert aux["Wavenumber"].shape == (19,) and aux["Wavenumber"].dtype == np.float32
        with pytest.raises(KeyError):
            _ = aux["PumpPower"]


def test_hyperspectral_side_datasets_are_per_pixel(hyperspectra_path: Path) -> None:
    with ptir5.open(hyperspectra_path) as f:
        averages = f.measurements[0].auxiliary["NumAverages"]
        assert averages.shape == (20, 20) and averages.dtype == np.int32


def test_spectrum_has_no_side_datasets(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        assert len(f.measurements[0].auxiliary) == 0


def test_side_dataset_reads_are_not_cached_and_need_an_open_file(
    optir_image_stack_path: Path,
) -> None:
    with ptir5.open(optir_image_stack_path) as f:
        m = f.measurements[0]
        first = m.auxiliary["Wavenumber"]
        first[:] = -1
        assert m.auxiliary["Wavenumber"][0] != -1
    with pytest.raises(FileClosedError):
        _ = m.auxiliary["Wavenumber"]


def test_completion_is_unknown_when_untracked(
    optir_image_stack_path: Path, hyperspectra_path: Path, flptir_stack_path: Path
) -> None:
    for path in (optir_image_stack_path, hyperspectra_path, flptir_stack_path):
        with ptir5.open(path) as f:
            assert f.measurements[0].component_completion is None


@pytest.mark.parametrize(("type_", "data", "completion", "expected"), [
    ("OPTIRHyperspectra", np.zeros((3, 2, 2), np.float32),
     np.array([[1, 0], [2, 1]], np.uint8), [[True, False], [False, True]]),
    ("TimeDomainCube", np.zeros((3, 1, 2), np.float32),
     np.array([[0, 1]], np.uint8), [[False, True]]),
    ("OPTIRImageStack", np.zeros((3, 2, 2), np.float32),
     np.array([1, 0, 255], np.uint8), [True, False, False]),
    ("FLPTIRImageStack", np.zeros((3, 2, 2), np.float32),
     np.array([0, 1, 1], np.uint8), [False, True, True]),
])
def test_completion_shape_follows_type_and_fails_closed(
    write_ptir: WritePtir, type_: str, data: np.ndarray, completion: np.ndarray,
    expected: list[object],
) -> None:
    path = write_ptir(type_, data, datasets={"ComponentCompletion": completion})
    with ptir5.open(path) as f:
        result = f.measurements[0].component_completion
        assert result is not None and result.dtype == np.bool_
        np.testing.assert_array_equal(result, expected)


@pytest.mark.parametrize("completion", [
    np.array([1, 1], np.uint8), np.array([1, 1, 1], np.int32), np.ones((3, 1), np.uint8),
])
def test_malformed_completion_raises(write_ptir: WritePtir, completion: np.ndarray) -> None:
    path = write_ptir("OPTIRImageStack", np.zeros((3, 2, 2), np.float32),
                      datasets={"ComponentCompletion": completion})
    with ptir5.open(path) as f:
        m = f.measurements[0]
        with pytest.raises(InvalidMeasurementError):
            _ = m.component_completion
