"""Derived output retains sources and round-trips values, coordinates and tree identity."""

from __future__ import annotations

import hashlib
import json
import stat
import sys
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


@pytest.mark.parametrize("variable_length", [False, True])
def test_utf8_metadata_retains_sdk_encoding(
    source: Path, tmp_path: Path, variable_length: bool
) -> None:
    """SDK readers must see wavenumbers and labels as UTF-8, not ASCII replacement bytes."""
    units = "cm⁻¹"
    with h5py.File(source, "r+") as file:
        stack = file[f"MEASUREMENTS/{GUID}"]
        del stack.attrs["XUnits"]
        stack.attrs.create(
            "XUnits",
            units if variable_length else units.encode("utf-8"),
            dtype=h5py.string_dtype("utf-8", None if variable_length else len(units.encode())),
        )
        for owner in (stack["Wavenumber"], file["TREE/NODES"]):
            owner.attrs.create("Description", "µm".encode(), dtype=h5py.string_dtype("utf-8", 3))
    before = source.read_bytes()
    output = tmp_path / "résultat.ptir"
    label = "O-PTIR — SPEND"
    guid = write(source, output, label=label, provenance={"notes": "Δ and µ"})
    assert source.read_bytes() == before
    with h5py.File(output, "r") as file:
        result = file[f"MEASUREMENTS/{guid}"]
        # PTIR Studio decodes with the HDF character-set flag, unlike the Python reader.
        for owner, key in (
            (result, "XUnits"),
            (result, "Label"),
            (result, "ProcessingProvenance"),
            (result["Wavenumber"], "Description"),
            (file["TREE/NODES"], "Description"),
            (file[f"TREE/{guid}"], "Label"),
            (file, "FilePath"),
        ):
            assert owner.attrs.get_id(key).get_type().get_cset() == h5py.h5t.CSET_UTF8
        raw_units = result.attrs["XUnits"]
        assert (raw_units if isinstance(raw_units, str) else raw_units.decode("utf-8")) == units
        assert result.attrs["Label"].decode("utf-8") == label
        np.testing.assert_array_equal(result["DATA"], np.arange(12).reshape(2, 2, 3) - 4)
        np.testing.assert_array_equal(result["Wavenumber"], [1004, 1008])


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
    real_hash = writer._sha256

    def altered_then_hashed(path: Path) -> str:
        # The first thing done to the snapshot is hashing it; alter it just before.
        with h5py.File(path, "r+") as file:
            file[f"MEASUREMENTS/{GUID}"].attrs["XUnits"] = np.bytes_(b"um")
        return real_hash(path)

    monkeypatch.setattr(writer, "_sha256", altered_then_hashed)
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


def test_result_mode_is_the_source_mode(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[int] = []
    real_chmod = writer.os.chmod

    def spy(path: Path, mode: int) -> None:
        calls.append(mode)
        real_chmod(path, mode)

    monkeypatch.setattr(writer.os, "chmod", spy)
    expected = stat.S_IMODE(source.stat().st_mode)
    write(source, tmp_path / "result.ptir")
    assert calls == [expected]


def test_mode_comes_from_the_snapshot_not_a_replaced_path(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Replacing the source path mid-write must not change the published permissions."""
    expected = stat.S_IMODE(source.stat().st_mode)
    real_hash = writer._sha256

    def replaced_then_hashed(path: Path) -> str:
        replacement = tmp_path / "replacement.ptir"
        replacement.write_bytes(b"unrelated")
        replacement.chmod(0o444)
        replacement.replace(source)
        return real_hash(path)

    monkeypatch.setattr(writer, "_sha256", replaced_then_hashed)
    output = tmp_path / "result.ptir"
    write(source, output)
    assert stat.S_IMODE(output.stat().st_mode) == expected


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_result_permissions_match_source(source: Path, tmp_path: Path) -> None:
    source.chmod(0o644)
    output = tmp_path / "result.ptir"
    write(source, output)
    assert stat.S_IMODE(output.stat().st_mode) == 0o644


def test_mode_is_applied_after_the_temporary_is_built(
    source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A read-only source mode must not reach the temporary before it is written."""
    events: list[str] = []
    real_append, real_chmod = writer.append_stack_result, writer.os.chmod

    def append(*args: object) -> None:
        events.append("append")
        real_append(*args)  # type: ignore[arg-type]

    def chmod(path: Path, mode: int) -> None:
        events.append("chmod")
        real_chmod(path, mode)

    monkeypatch.setattr(writer, "append_stack_result", append)
    monkeypatch.setattr(writer.os, "chmod", chmod)
    write(source, tmp_path / "result.ptir")
    assert events == ["append", "chmod"]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_read_only_source_still_produces_a_result(source: Path, tmp_path: Path) -> None:
    source.chmod(0o444)
    output = tmp_path / "result.ptir"
    write(source, output)
    assert stat.S_IMODE(output.stat().st_mode) == 0o444


@pytest.mark.parametrize("group", ["MEASUREMENTS", "TREE"])
def test_external_link_to_format_group_is_rejected(
    source: Path, tmp_path: Path, group: str
) -> None:
    other = tmp_path / "other.h5"
    with h5py.File(source, "r+") as file, h5py.File(other, "w") as target:
        file.copy(group, target)
        del file[group]
        file[group] = h5py.ExternalLink(other.name, f"/{group}")
    before = other.read_bytes()
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="local object"):
        write(source, output)
    assert other.read_bytes() == before
    assert not output.exists()
    assert list(tmp_path.glob(".ptir5-result-*")) == []


@pytest.mark.parametrize("child", ["NumAverages", "DATA", "Channel"])
def test_external_link_to_stack_child_is_rejected(
    source: Path, tmp_path: Path, child: str
) -> None:
    other = tmp_path / "other.h5"
    path = f"MEASUREMENTS/{GUID}"
    with h5py.File(source, "r+") as file, h5py.File(other, "w") as target:
        file.copy(f"{path}/{child}", target, name=child)
        del file[f"{path}/{child}"]
        file[f"{path}/{child}"] = h5py.ExternalLink(other.name, f"/{child}")
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="local object"):
        write(source, output)
    assert not output.exists()
    assert list(tmp_path.glob(".ptir5-result-*")) == []


@pytest.mark.parametrize("kind", ["soft", "external"])
def test_linked_tree_node_is_rejected(source: Path, tmp_path: Path, kind: str) -> None:
    """Retained tree leaves are part of the snapshot and must not be links."""
    other = tmp_path / "other.h5"
    with h5py.File(source, "r+") as file, h5py.File(other, "w") as target:
        file.copy(f"TREE/{GUID}", target, name="leaf")
        file.copy(f"TREE/{GUID}", file["TREE"], name="spare")
        del file[f"TREE/{GUID}"]
        file[f"TREE/{GUID}"] = (
            h5py.SoftLink("/TREE/spare")
            if kind == "soft"
            else h5py.ExternalLink(other.name, "/leaf")
        )
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="local object"):
        write(source, output)
    assert not output.exists()
    assert list(tmp_path.glob(".ptir5-result-*")) == []


def test_hard_link_cycle_does_not_hang(source: Path, tmp_path: Path) -> None:
    with h5py.File(source, "r+") as file:
        file[f"MEASUREMENTS/{GUID}/Channel/loop"] = file["MEASUREMENTS"]
    # The cycle is a nested member, so it is rejected (and the walk terminates).
    with pytest.raises(ValueError, match="nested members"):
        write(source, tmp_path / "result.ptir")


@pytest.mark.parametrize("kind", ["external", "virtual"])
def test_dataset_with_out_of_file_storage_is_rejected(
    source: Path, tmp_path: Path, kind: str
) -> None:
    """Payloads outside the .ptir are not covered by its checksum."""
    path = f"MEASUREMENTS/{GUID}/NumAverages"
    sidecar = tmp_path / "sidecar.bin"
    sidecar.write_bytes(np.arange(4, dtype=np.int32).tobytes())
    with h5py.File(source, "r+") as file:
        del file[path]
        if kind == "external":
            file.create_dataset(path, shape=(4,), dtype=np.int32, external=[(sidecar.name, 0, 16)])
        else:
            layout = h5py.VirtualLayout(shape=(4,), dtype=np.int32)
            layout[:] = h5py.VirtualSource(sidecar.name, "data", shape=(4,))
            file.create_virtual_dataset(path, layout, fillvalue=0)
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="in the file"):
        write(source, output)
    assert not output.exists()
    assert list(tmp_path.glob(".ptir5-result-*")) == []


def test_tree_nodes_attributes_are_preserved(source: Path, tmp_path: Path) -> None:
    with h5py.File(source, "r+") as file:
        file["TREE/NODES"].attrs["IndexVersion"] = np.array([3], dtype=np.int32)
        file["TREE/NODES"].attrs["Note"] = np.bytes_(b"keep me")
    output = tmp_path / "result.ptir"
    write(source, output)
    with h5py.File(output, "r") as file:
        attrs = file["TREE/NODES"].attrs
        assert attrs["IndexVersion"][0] == 3
        assert bytes(attrs["Note"]) == b"keep me"
        assert file["TREE/NODES"].shape == (2, 16)


def test_per_frame_dataset_attributes_are_preserved(source: Path, tmp_path: Path) -> None:
    with h5py.File(source, "r+") as file:
        stack = file[f"MEASUREMENTS/{GUID}"]
        stack["Wavenumber"].attrs["Units"] = np.bytes_(b"cm-1")
        stack["NumAverages"].attrs["Calibration"] = np.array([2.5], dtype=np.float64)
    output = tmp_path / "result.ptir"
    guid = write(source, output)
    with h5py.File(output, "r") as file:
        group = file[f"MEASUREMENTS/{guid}"]
        assert bytes(group["Wavenumber"].attrs["Units"]) == b"cm-1"
        assert group["NumAverages"].attrs["Calibration"][0] == 2.5


def test_overflowing_axis_coordinates_are_rejected(source: Path, tmp_path: Path) -> None:
    with h5py.File(source, "r+") as file:
        stack = file[f"MEASUREMENTS/{GUID}"]
        stack.attrs["XStart"] = np.array([1e308], dtype=np.float64)
        stack.attrs["XIncrement"] = np.array([1e308], dtype=np.float64)
        del stack["Wavenumber"]
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="must be finite"):
        write(source, output)
    assert not output.exists()
    assert list(tmp_path.glob(".ptir5-result-*")) == []


def test_rebased_start_overflowing_stored_precision_is_rejected(
    source: Path, tmp_path: Path
) -> None:
    """Finite in float64 but infinite once stored in the attribute's float32."""
    with h5py.File(source, "r+") as file:
        stack = file[f"MEASUREMENTS/{GUID}"]
        stack.attrs["XStart"] = np.array([3e38], dtype=np.float32)
        stack.attrs["XIncrement"] = np.array([3e38], dtype=np.float32)
        del stack["Wavenumber"]
    output = tmp_path / "result.ptir"
    with pytest.raises(ValueError, match="must be finite"):
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
