"""Tests for PTIR5File lifecycle and basic operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import ptir5
from ptir5 import FileClosedError, PTIR5File

if TYPE_CHECKING:
    from pathlib import Path


def test_open_and_close(optir_spectrum_path: Path) -> None:
    f = ptir5.open(optir_spectrum_path)
    assert f.is_open
    assert f.path == str(optir_spectrum_path)
    f.close()
    assert not f.is_open


def test_context_manager(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        assert f.is_open
    assert not f.is_open


def test_access_after_close_raises(optir_spectrum_path: Path) -> None:
    f = ptir5.open(optir_spectrum_path)
    f.close()
    with pytest.raises(FileClosedError):
        _ = f.measurements


def test_repr_open(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        r = repr(f)
        assert "open" in r
        assert "sample_optir_spectrum.ptir" in r


def test_repr_closed(optir_spectrum_path: Path) -> None:
    f = ptir5.open(optir_spectrum_path)
    f.close()
    assert "closed" in repr(f)


def test_ptir5file_direct_construction(optir_spectrum_path: Path) -> None:
    with PTIR5File(optir_spectrum_path) as f:
        assert f.is_open
        assert len(f.measurements) > 0


def test_all_fixtures_open(fixtures_dir: Path) -> None:
    """Verify every fixture file opens successfully."""
    ptir_files = list(fixtures_dir.glob("*.ptir"))
    assert len(ptir_files) == 8
    for p in ptir_files:
        with ptir5.open(p) as f:
            assert f.is_open
            assert len(f.measurements) >= 1
