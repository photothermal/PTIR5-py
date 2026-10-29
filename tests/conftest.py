"""Pytest fixtures for ptir5 tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import h5py
import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

FIXTURES_DIR = Path(__file__).parent / "fixtures"

MEASUREMENT_GUID = "11111111-2222-3333-4444-555555555555"


@pytest.fixture
def write_ptir(tmp_path: Path) -> Callable[..., Path]:
    """Return a writer for a synthetic one-measurement PTIR5 file (no TREE)."""

    def write(
        type_: str,
        data: np.ndarray | None,
        *,
        attrs: Mapping[str, object] | None = None,
        datasets: Mapping[str, np.ndarray] | None = None,
        generated: Sequence[tuple[str, np.ndarray, Mapping[str, object]]] = (),
        filename: str = "synthetic.ptir",
    ) -> Path:
        path = tmp_path / filename
        with h5py.File(path, "w") as h5:
            h5.attrs["DocType"] = np.bytes_(b"PTIR5")
            h5.create_group("BACKGROUNDS")
            group = h5.create_group(f"MEASUREMENTS/{MEASUREMENT_GUID}")
            _populate(group, type_, data, attrs or {})
            for name, values in (datasets or {}).items():
                group.create_dataset(name, data=values)
            for index, (child_type, child_data, child_attrs) in enumerate(generated):
                child = group.create_group(f"GENERATED/00000000-0000-0000-0000-{index:012d}")
                _populate(child, child_type, child_data, child_attrs)
        return path

    return write


def _populate(
    group: h5py.Group, type_: str, data: np.ndarray | None, attrs: Mapping[str, object]
) -> None:
    group.attrs["TYPE"] = np.bytes_(type_.encode())
    for name, value in attrs.items():
        group.attrs[name] = value
    if data is not None:
        group.create_dataset("DATA", data=data)


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def optir_spectrum_path() -> Path:
    return FIXTURES_DIR / "sample_optir_spectrum.ptir"


@pytest.fixture
def raman_spectrum_path() -> Path:
    return FIXTURES_DIR / "sample_raman_spectrum.ptir"


@pytest.fixture
def optir_image_path() -> Path:
    return FIXTURES_DIR / "sample_optir_image.ptir"


@pytest.fixture
def camera_image_path() -> Path:
    return FIXTURES_DIR / "sample_camera_image.ptir"


@pytest.fixture
def flptir_image_path() -> Path:
    return FIXTURES_DIR / "sample_flptir_image.ptir"


@pytest.fixture
def flptir_stack_path() -> Path:
    return FIXTURES_DIR / "sample_flptir_stack.ptir"


@pytest.fixture
def optir_image_stack_path() -> Path:
    return FIXTURES_DIR / "sample_optir_image_stack.ptir"


@pytest.fixture
def hyperspectra_path() -> Path:
    return FIXTURES_DIR / "sample_optir_hyperspectra_generated_spectrum_generated_image.ptir"
