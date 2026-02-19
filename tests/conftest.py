"""Pytest fixtures for ptir5 tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
