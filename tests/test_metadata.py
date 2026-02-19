"""Tests for MetadataView attribute reading."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ptir5

if TYPE_CHECKING:
    from pathlib import Path


def test_metadata_contains_type(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        assert "TYPE" in m.metadata
        assert m.metadata["TYPE"] == "OPTIRSpectrum"


def test_metadata_label(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        assert m.metadata["Label"] == "O-PTIR0 1"
        assert m.label == "O-PTIR0 1"


def test_metadata_numeric_values(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        assert isinstance(m.metadata["XStart"], float)
        assert isinstance(m.metadata["XIncrement"], float)
        assert m.metadata["XStart"] == 962.0
        assert m.metadata["XIncrement"] == 2.0


def test_metadata_string_values(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        assert m.metadata["XUnits"] == "cm-1"


def test_metadata_channel_subgroup(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        # Channel sub-group attributes are prefixed with "Channel."
        assert "Channel.Units" in m.metadata
        assert m.metadata["Channel.Units"] == "mV"


def test_metadata_get_method(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        assert m.metadata.get("TYPE") == "OPTIRSpectrum"
        assert m.metadata.get("NonExistentKey") is None
        assert m.metadata.get("NonExistentKey", "default") == "default"


def test_metadata_keys_values_items(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        keys = list(m.metadata.keys())
        assert len(keys) > 0
        assert "TYPE" in keys
        values = list(m.metadata.values())
        assert len(values) == len(keys)
        items = list(m.metadata.items())
        assert len(items) == len(keys)


def test_metadata_dict_conversion(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        d = dict(m.metadata)
        assert isinstance(d, dict)
        assert d["TYPE"] == "OPTIRSpectrum"


def test_metadata_len(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        assert len(m.metadata) > 10  # Should have many attributes


def test_metadata_particle_data(optir_spectrum_path: Path) -> None:
    """sample_optir_spectrum has an empty ParticleData sub-group."""
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        # ParticleData exists but is empty, so no ParticleData.* keys
        particle_keys = [k for k in m.metadata if k.startswith("ParticleData.")]
        assert len(particle_keys) == 0


def test_metadata_image_attributes(optir_image_path: Path) -> None:
    with ptir5.open(optir_image_path) as f:
        m = f.measurements[0]
        assert "ImageWidth" in m.metadata
        assert "ImageHeight" in m.metadata
        assert isinstance(m.metadata["ImageWidth"], float)
        assert m.metadata["ImageWidth"] == 50.0
        assert m.metadata["ImageHeight"] == 50.0


def test_metadata_cached(optir_spectrum_path: Path) -> None:
    """Accessing metadata twice should return same cached dict."""
    with ptir5.open(optir_spectrum_path) as f:
        m = f.measurements[0]
        _ = m.metadata["TYPE"]
        _ = m.metadata["Label"]
        # Internal cache should be populated after first access
        assert m.metadata._cache is not None
