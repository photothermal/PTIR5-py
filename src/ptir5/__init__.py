"""ptir5 — Read-only Python library for PTIR5 files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ptir5._version import __version__
from ptir5.enums import DataShape, MeasurementType, PixelFormat
from ptir5.exceptions import (
    FileClosedError,
    InvalidMeasurementError,
    MeasurementNotFoundError,
    PTIR5Error,
)
from ptir5.file import PTIR5File
from ptir5.metadata import MetadataView
from ptir5.models import (
    ByteImage2D,
    ByteImageStack3D,
    CameraImage,
    CameraImageStack,
    FloatHypercube3D,
    FloatImage2D,
    FloatSpectrum1D,
    FLPTIRImage,
    FLPTIRImageStack,
    FluorescenceImage,
    GeneratedImage,
    GeneratedSpectrum,
    Measurement,
    OPTIRHyperspectra,
    OPTIRImage,
    OPTIRImageStack,
    OPTIRSpectrum,
    PTSRSImage,
    PTSRSImageStack,
    PTSRSSpectrum,
    RamanHyperspectra,
    RamanSpectrum,
)
from ptir5.tree import TreeFolder, TreeLeaf, TreeRoot

if TYPE_CHECKING:
    from pathlib import Path


def open(path: str | Path) -> PTIR5File:
    """Open a PTIR5 file for reading.

    Use as a context manager::

        with ptir5.open("sample.ptir") as f:
            for m in f.measurements:
                print(m.label)
    """
    return PTIR5File(path)


__all__ = [
    "__version__",
    "open",
    # File
    "PTIR5File",
    # Enums
    "DataShape",
    "MeasurementType",
    "PixelFormat",
    # Exceptions
    "FileClosedError",
    "InvalidMeasurementError",
    "MeasurementNotFoundError",
    "PTIR5Error",
    # Models
    "Measurement",
    "FloatSpectrum1D",
    "FloatImage2D",
    "ByteImage2D",
    "FloatHypercube3D",
    "ByteImageStack3D",
    "OPTIRSpectrum",
    "RamanSpectrum",
    "GeneratedSpectrum",
    "PTSRSSpectrum",
    "OPTIRImage",
    "GeneratedImage",
    "PTSRSImage",
    "CameraImage",
    "FluorescenceImage",
    "FLPTIRImage",
    "OPTIRHyperspectra",
    "RamanHyperspectra",
    "OPTIRImageStack",
    "CameraImageStack",
    "FLPTIRImageStack",
    "PTSRSImageStack",
    # Metadata
    "MetadataView",
    # Tree
    "TreeRoot",
    "TreeFolder",
    "TreeLeaf",
]
