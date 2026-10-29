"""Side datasets stored next to DATA, and opt-in component-completion tracking.

Spec §4.3 places per-pixel and per-image auxiliary arrays beside ``DATA``;
§7.4.1 defines ``ComponentCompletion`` (absent = unknown, 1 = complete, any
other value = incomplete, fail closed).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import h5py
import numpy as np
import pytest

import ptir5
from ptir5 import FileClosedError, InvalidMeasurementError
from ptir5._reader import HDF5Reader

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


def test_side_dataset_and_scalar_attribute_with_one_name_stay_separate(
    write_ptir: WritePtir,
) -> None:
    path = write_ptir("OPTIRImageStack", np.zeros((3, 2, 2), np.float32),
                      attrs={"NumAverages": np.int32(8)},
                      datasets={"NumAverages": np.array([8, 7, 8], np.int32)})
    with ptir5.open(path) as f:
        m = f.measurements[0]
        assert m.metadata["NumAverages"] == 8
        np.testing.assert_array_equal(m.auxiliary["NumAverages"], [8, 7, 8])


@pytest.mark.parametrize("member", ["group", "dangling soft link"])
def test_completion_member_that_is_not_a_dataset_raises(
    write_ptir: WritePtir, member: str
) -> None:
    path = write_ptir("OPTIRImageStack", np.zeros((3, 2, 2), np.float32))
    with h5py.File(path, "a") as h5:
        stack = h5["MEASUREMENTS/11111111-2222-3333-4444-555555555555"]
        if member == "group":
            stack.create_group("ComponentCompletion")
        else:
            stack["ComponentCompletion"] = h5py.SoftLink("/missing/ComponentCompletion")
    with ptir5.open(path) as f:
        m = f.measurements[0]
        with pytest.raises(InvalidMeasurementError, match="ComponentCompletion"):
            _ = m.component_completion


def test_side_dataset_names_are_listed_once_per_measurement(
    optir_image_stack_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    original = HDF5Reader.list_datasets

    def counting(self: HDF5Reader, path: str) -> list[str]:
        calls.append(path)
        return original(self, path)

    monkeypatch.setattr(HDF5Reader, "list_datasets", counting)
    with ptir5.open(optir_image_stack_path) as f:
        m = f.measurements[0]
        _ = m.auxiliary["Wavenumber"]
        _ = m.auxiliary["NumAverages"]
        assert "TopFocus" in m.auxiliary and len(m.auxiliary) == 11
    assert len(calls) == 1
