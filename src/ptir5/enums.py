"""Enumerations for PTIR5 measurement types, data shapes, and pixel formats."""

from __future__ import annotations

from enum import Enum, IntEnum, StrEnum


class MeasurementType(StrEnum):
    """Measurement type identifiers matching the TYPE attribute in PTIR5 files."""

    OPTIRSpectrum = "OPTIRSpectrum"
    RamanSpectrum = "RamanSpectrum"
    GeneratedSpectrum = "GeneratedSpectrum"
    PTSRSSpectrum = "PTSRSSpectrum"
    OPTIRImage = "OPTIRImage"
    GeneratedImage = "GeneratedImage"
    PTSRSImage = "PTSRSImage"
    CameraImage = "CameraImage"
    FluorescenceImage = "FluorescenceImage"
    FLPTIRImage = "FLPTIRImage"
    OPTIRHyperspectra = "OPTIRHyperspectra"
    RamanHyperspectra = "RamanHyperspectra"
    OPTIRImageStack = "OPTIRImageStack"
    CameraImageStack = "CameraImageStack"
    FLPTIRImageStack = "FLPTIRImageStack"
    PTSRSImageStack = "PTSRSImageStack"


class DataShape(Enum):
    """Fundamental data shapes for measurement data arrays."""

    FLOAT_SPECTRUM_1D = "float_spectrum_1d"
    FLOAT_IMAGE_2D = "float_image_2d"
    BYTE_IMAGE_2D = "byte_image_2d"
    FLOAT_HYPERCUBE_3D = "float_hypercube_3d"
    BYTE_IMAGE_STACK_3D = "byte_image_stack_3d"


class PixelFormat(IntEnum):
    """Pixel format identifiers for camera/byte image data."""

    Default = 0
    Extended = 0
    Indexed1 = 1
    Indexed2 = 2
    Indexed4 = 3
    Indexed8 = 4
    BlackWhite = 5
    Gray2 = 6
    Gray4 = 7
    Gray8 = 8
    Bgr555 = 9
    Bgr565 = 10
    Gray16 = 11
    Bgr24 = 12
    Rgb24 = 13
    Bgr32 = 14
    Bgra32 = 15
    Pbgra32 = 16
    Gray32Float = 17
    Bgr101010 = 20
    Rgb48 = 21
    Rgba64 = 22
    Prgba64 = 23
    Rgba128Float = 25
    Prgba128Float = 26
    Rgb128Float = 27
    Cmyk32 = 28


# Mapping from MeasurementType to DataShape
TYPE_TO_SHAPE: dict[MeasurementType, DataShape] = {
    MeasurementType.OPTIRSpectrum: DataShape.FLOAT_SPECTRUM_1D,
    MeasurementType.RamanSpectrum: DataShape.FLOAT_SPECTRUM_1D,
    MeasurementType.GeneratedSpectrum: DataShape.FLOAT_SPECTRUM_1D,
    MeasurementType.PTSRSSpectrum: DataShape.FLOAT_SPECTRUM_1D,
    MeasurementType.OPTIRImage: DataShape.FLOAT_IMAGE_2D,
    MeasurementType.GeneratedImage: DataShape.FLOAT_IMAGE_2D,
    MeasurementType.PTSRSImage: DataShape.FLOAT_IMAGE_2D,
    MeasurementType.CameraImage: DataShape.BYTE_IMAGE_2D,
    MeasurementType.FluorescenceImage: DataShape.BYTE_IMAGE_2D,
    MeasurementType.FLPTIRImage: DataShape.BYTE_IMAGE_2D,
    MeasurementType.OPTIRHyperspectra: DataShape.FLOAT_HYPERCUBE_3D,
    MeasurementType.RamanHyperspectra: DataShape.FLOAT_HYPERCUBE_3D,
    MeasurementType.OPTIRImageStack: DataShape.FLOAT_HYPERCUBE_3D,
    MeasurementType.CameraImageStack: DataShape.BYTE_IMAGE_STACK_3D,
    MeasurementType.FLPTIRImageStack: DataShape.BYTE_IMAGE_STACK_3D,
    MeasurementType.PTSRSImageStack: DataShape.FLOAT_HYPERCUBE_3D,
}
