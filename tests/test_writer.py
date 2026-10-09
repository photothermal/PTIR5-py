"""Derived output retains sources and round-trips values, coordinates and tree identity."""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from typing import TYPE_CHECKING

import h5py
import numpy as np
import pytest

import ptir5
from ptir5 import writer

if TYPE_CHECKING:
    from pathlib import Path


GUID = "12345678-1234-1234-1234-1234567890ab"


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "source.ptir"
    with h5py.File(path, "w") as file:
        file.attrs["DocType"] = np.bytes_(b"PTIR5")
        stack = file.create_group(f"MEASUREMENTS/{GUID}")
        stack.attrs["TYPE"] = np.bytes_(b"OPTIRImageStack")
        stack.attrs["Label"] = np.bytes_(b"DC")
        stack.attrs["XStart"] = np.array([1000], dtype=np.float32)
        stack.attrs["XIncrement"] = np.array([4], dtype=np.float32)
        stack.attrs["XUnits"] = np.bytes_(b"cm-1")
        stack.attrs["ImageWidth"] = np.array([5], dtype=np.float32)
        stack.attrs["MinValue"] = np.array([-999], dtype=np.float32)
        stack.attrs["PaletteMinValue"] = np.array([-999], dtype=np.float32)
        data = np.arange(24, dtype=np.float32).reshape(4, 2, 3)
        data[-1] = np.nan
        stack.create_dataset("DATA", data=data)
        stack.create_dataset("Wavenumber", data=np.arange(4, dtype=np.float32) * 4 + 1000)
        stack.create_dataset("NumAverages", data=np.arange(4, dtype=np.int32))
        stack.create_dataset("MinValue", data=np.full(4, -999, dtype=np.float32))
        stack.create_dataset("MaxValue", data=np.full(4, 999, dtype=np.float32))
        stack.create_dataset("ComponentCompletion", data=np.array([1, 1, 1, 0], dtype=np.uint8))
        stack.create_group("Channel").attrs["Units"] = np.bytes_(b"V")
        cached = stack.create_group("GENERATED/old-cache")
        cached.attrs["TYPE"] = np.bytes_(b"GeneratedImage")
        cached.create_dataset("DATA", data=np.zeros((2, 3), dtype=np.float32))
        file.create_group("BACKGROUNDS")
        tree = file.create_group("TREE")
        tree.create_dataset(
            "NODES", data=np.frombuffer(uuid.UUID(GUID).bytes_le, dtype=np.uint8).reshape(1, 16)
        )
        leaf = tree.create_group(GUID)
        leaf.attrs["TYPE"] = np.bytes_(b"OPTIRImageStack")
        leaf.attrs["Label"] = np.bytes_(b"DC")
    return path


def write(source: Path, output: Path, **kwargs: object) -> str:
    data = np.arange(12, dtype=np.float32).reshape(2, 2, 3) - 4
    defaults = {"frame_start": 1, "label": "DC — SPEND", "provenance": {"method": "test"}}
    defaults.update(kwargs)
    return ptir5.write_image_stack_result(source, output, GUID, data, **defaults)  # type: ignore[arg-type]


def test_result_round_trip_preserves_source_and_recomputes_caches(
    source: Path, tmp_path: Path
) -> None:
    before = source.read_bytes()
    output = tmp_path / "result.ptir"
    guid = write(source, output)
    assert guid != GUID
    assert source.read_bytes() == before
    with ptir5.open(source) as raw, ptir5.open(output) as saved:
        original = raw.get_measurement(GUID)
        preserved = saved.get_measurement(GUID)
        np.testing.assert_array_equal(original.data, preserved.data)
        assert dict(original.metadata) == dict(preserved.metadata)
        assert len(preserved.generated) == 1
        result = saved.get_measurement(guid)
        assert result.label == "DC — SPEND"
        np.testing.assert_array_equal(
            result.data, np.arange(12, dtype=np.float32).reshape(2, 2, 3) - 4
        )
        np.testing.assert_array_equal(result.x_values, [1004, 1008])  # type: ignore[attr-defined]
        assert result.metadata["Channel.Units"] == "V"
        assert result.metadata["ImageWidth"] == 5
        assert result.metadata["MinValue"] == -4
        assert result.metadata["MaxValue"] == 7
        assert "PaletteMinValue" not in result.metadata
        assert result.generated == ()
        provenance = json.loads(result.metadata["ProcessingProvenance"])
        assert provenance["source_sha256"] == hashlib.sha256(before).hexdigest()
        assert provenance["source_frame_range"] == [1, 3]
        assert provenance["source_measurement_guid"] == GUID
        assert provenance["result_measurement_guid"] == guid
        assert saved.tree is not None
        assert {leaf.guid for _, _, leaves in saved.tree.walk() for leaf in leaves} == {GUID, guid}
    with h5py.File(output, "r") as file:
        group = file[f"MEASUREMENTS/{guid}"]
        np.testing.assert_array_equal(group["MinValue"], [-4, 2])
        np.testing.assert_array_equal(group["MaxValue"], [1, 7])
        np.testing.assert_array_equal(group["Wavenumber"], [1004, 1008])
        np.testing.assert_array_equal(group["NumAverages"], [1, 2])
        np.testing.assert_array_equal(group["ComponentCompletion"], [1, 1])


def test_inexact_float32_increment_is_accepted(source: Path, tmp_path: Path) -> None:
    """Wavenumbers rounded to float32 must still match a regular float64 axis."""
    with h5py.File(source, "r+") as file:
        stack = file[f"MEASUREMENTS/{GUID}"]
        stack.attrs["XIncrement"] = np.array([0.1], dtype=np.float32)
        wavenumbers = np.float32(1000) + np.arange(4, dtype=np.float32) * np.float32(0.1)
        del stack["Wavenumber"]
        stack.create_dataset("Wavenumber", data=wavenumbers)
    output = tmp_path / "result.ptir"
    guid = write(source, output)
    with ptir5.open(source) as raw, ptir5.open(output) as saved:
        expected = raw.get_measurement(GUID).x_values[1:3]  # type: ignore[attr-defined]
        np.testing.assert_allclose(
            saved.get_measurement(guid).x_values,  # type: ignore[attr-defined]
            expected,
            rtol=0,
            atol=1e-3,
        )


def test_rebased_xstart_keeps_source_precision_without_wavenumber(
    source: Path, tmp_path: Path
) -> None:
    """A float64 XStart with an inexact increment must not be coarsened to float32."""
    with h5py.File(source, "r+") as file:
        stack = file[f"MEASUREMENTS/{GUID}"]
        stack.attrs["XStart"] = np.array([1000.123456789], dtype=np.float64)
        stack.attrs["XIncrement"] = np.array([0.1], dtype=np.float64)
        del stack["Wavenumber"]
    output = tmp_path / "result.ptir"
    guid = write(source, output)
    with ptir5.open(source) as raw, ptir5.open(output) as saved:
        expected = raw.get_measurement(GUID).x_values[1:3]  # type: ignore[attr-defined]
        np.testing.assert_allclose(
            saved.get_measurement(guid).x_values,  # type: ignore[attr-defined]
            expected,
            rtol=0,
            atol=1e-9,
        )
    with h5py.File(output, "r") as file:
        assert file[f"MEASUREMENTS/{guid}"].attrs["XStart"].dtype == np.float64


def test_validation_runs_on_the_copied_snapshot(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A source swapped after the caller's call began must not be published unvalidated."""
    real_copy = shutil.copyfile

    def swapped_copy(src: Path, dst: Path) -> Path:
        real_copy(src, dst)
        with h5py.File(dst, "r+") as file:
            file[f"MEASUREMENTS/{GUID}"].attrs["XUnits"] = np.bytes_(b"um")
        return dst

    monkeypatch.setattr(writer.shutil, "copyfile", swapped_copy)
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="wavenumber axis"):
        write(source, output)
    assert not output.exists()
    assert list(tmp_path.glob(".ptir5-result-*")) == []


@pytest.mark.parametrize("name", ["Channel", "Palette", "GENERATED"])
def test_known_subgroup_that_is_a_dataset_is_rejected(
    source: Path, tmp_path: Path, name: str
) -> None:
    with h5py.File(source, "r+") as file:
        stack = file[f"MEASUREMENTS/{GUID}"]
        if name in stack:
            del stack[name]
        stack.create_dataset(name, data=np.zeros(2, dtype=np.float32))
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="must be a group"):
        write(source, output)
    assert not output.exists()
    assert list(tmp_path.glob(".ptir5-result-*")) == []


@pytest.mark.parametrize("name", ["Channel", "Palette"])
def test_metadata_group_with_nested_members_is_rejected(
    source: Path, tmp_path: Path, name: str
) -> None:
    with h5py.File(source, "r+") as file:
        stack = file[f"MEASUREMENTS/{GUID}"]
        group = stack.require_group(name)
        group.create_dataset("FrameCache", data=np.zeros(4, dtype=np.float32))
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="nested members"):
        write(source, output)
    assert not output.exists()
    assert list(tmp_path.glob(".ptir5-result-*")) == []


@pytest.mark.parametrize("failure", ["nonfinite", "dtype", "rank", "spatial", "empty"])
def test_invalid_data_creates_no_output(source: Path, tmp_path: Path, failure: str) -> None:
    data = np.ones((2, 2, 3), dtype=np.float32)
    if failure == "nonfinite":
        data[0, 0, 0] = np.nan
    elif failure == "dtype":
        data = data.astype(np.float64)
    elif failure == "rank":
        data = data[0]
    elif failure == "spatial":
        data = data[:, :, :2]
    else:
        data = data[:0]
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError):
        ptir5.write_image_stack_result(source, output, GUID, data, label="Result", provenance={})
    assert not output.exists()
    assert not list(tmp_path.glob(".ptir5-result-*"))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"frame_start": -1},
        {"frame_start": 3},
        {"frame_start": True},
        {"label": ""},
        {"label": "a\x00b"},
        {"provenance": {"bad": float("nan")}},
    ],
)
def test_invalid_selection_and_provenance_fail_without_output(
    source: Path, tmp_path: Path, kwargs: dict[str, object]
) -> None:
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError):
        write(source, output, **kwargs)
    assert not output.exists()


def test_existing_output_and_input_are_never_overwritten(source: Path, tmp_path: Path) -> None:
    original = source.read_bytes()
    with pytest.raises(FileExistsError):
        write(source, source)
    assert source.read_bytes() == original
    output = tmp_path / "result.ptir"
    output.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        write(source, output)
    assert output.read_bytes() == b"existing"


@pytest.mark.parametrize(
    "malformation", ["child", "frame_metadata", "tree", "doctype", "axis", "wavenumbers"]
)
def test_malformed_source_cleans_temporary(
    source: Path, tmp_path: Path, malformation: str
) -> None:
    with h5py.File(source, "r+") as file:
        group = file[f"MEASUREMENTS/{GUID}"]
        if malformation == "child":
            group.create_group("UnknownCache")
        elif malformation == "frame_metadata":
            del group["NumAverages"]
            group.create_dataset("NumAverages", data=np.zeros(1))
        elif malformation == "tree":
            del file["TREE/NODES"]
        elif malformation == "doctype":
            file.attrs["DocType"] = np.bytes_(b"OTHER")
        elif malformation == "wavenumbers":
            group["Wavenumber"][1] = 1500
        else:
            group.attrs["XUnits"] = np.bytes_(b"s")
    before = source.read_bytes()
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError):
        write(source, output)
    assert source.read_bytes() == before
    assert not output.exists()
    assert not list(tmp_path.glob(".ptir5-result-*"))


def test_expected_source_hash_rejects_wrong_acquisition(source: Path, tmp_path: Path) -> None:
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="checksum"):
        write(source, output, expected_source_sha256="different-acquisition")
    assert not output.exists()


def test_failed_append_preserves_source_and_cleans_temporary(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = source.read_bytes()
    output = tmp_path / "result.ptir"

    def fail(*args: object) -> None:
        raise OSError("Injected write failure")

    monkeypatch.setattr(writer, "append_stack_result", fail)
    with pytest.raises(OSError, match="Injected write failure"):
        write(source, output)
    assert source.read_bytes() == before
    assert not output.exists()
    assert not list(tmp_path.glob(".ptir5-result-*"))


def test_publish_race_preserves_other_output(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "result.ptir"
    original_link = writer.os.link

    def occupied(src: object, dest: object) -> None:
        output.write_bytes(b"other process")
        original_link(src, dest)  # type: ignore[arg-type]

    monkeypatch.setattr(writer.os, "link", occupied)
    with pytest.raises(FileExistsError):
        write(source, output)
    assert output.read_bytes() == b"other process"
    assert not list(tmp_path.glob(".ptir5-result-*"))
