"""Data model classes for PTIR5 measurements.

Hierarchy:
    Measurement (base)
    ├── FloatSpectrum1D    — 1D float spectra
    ├── FloatImage2D       — 2D float images (OPTIR, Generated, PTSRS)
    ├── ByteImage2D        — 2D byte images (Camera, Fluorescence, FLPTIR)
    ├── FloatHypercube3D   — 3D float cubes (Hyperspectra, OPTIRImageStack)
    └── ByteImageStack3D   — 3D byte stacks (CameraImageStack, FLPTIRImageStack)

Each base shape has concrete subclasses for each MeasurementType.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ptir5.enums import TYPE_TO_SHAPE, DataShape, MeasurementType, PixelFormat

if TYPE_CHECKING:
    from ptir5._reader import HDF5Reader
    from ptir5.metadata import MetadataView


class Measurement:
    """Base class for all PTIR5 measurements."""

    __slots__ = (
        "_guid",
        "_measurement_type",
        "_data_shape",
        "_hdf5_path",
        "_reader",
        "_metadata",
        "_generated",
    )

    def __init__(
        self,
        guid: str,
        measurement_type: MeasurementType | str,
        data_shape: DataShape,
        hdf5_path: str,
        reader: HDF5Reader,
        metadata: MetadataView,
        generated: tuple[Measurement, ...] = (),
    ) -> None:
        self._guid = guid
        self._measurement_type = (
            measurement_type
            if isinstance(measurement_type, MeasurementType)
            else str(measurement_type)
        )
        self._data_shape = data_shape
        self._hdf5_path = hdf5_path
        self._reader = reader
        self._metadata = metadata
        self._generated = generated

    @property
    def guid(self) -> str:
        return self._guid

    @property
    def measurement_type(self) -> MeasurementType | str:
        return self._measurement_type

    @property
    def data_shape(self) -> DataShape:
        return self._data_shape

    @property
    def label(self) -> str:
        val: Any = self._metadata.get("Label", "")
        return str(val)

    @property
    def metadata(self) -> MetadataView:
        return self._metadata

    @property
    def generated(self) -> tuple[Measurement, ...]:
        return self._generated

    @property
    def data(self) -> np.ndarray[Any, Any]:
        """Read the DATA dataset. Not cached — assign to a variable to reuse."""
        return self._reader.read_dataset(f"{self._hdf5_path}/DATA")

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} guid={self._guid!r} "
            f"type={self._measurement_type!r} label={self.label!r}>"
        )


# ---------------------------------------------------------------------------
# Base shape classes
# ---------------------------------------------------------------------------


class FloatSpectrum1D(Measurement):
    """1D float spectrum — shape (length,), dtype float32."""

    @property
    def num_points(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[0]

    @property
    def x_start(self) -> float:
        return float(self._metadata.get("XStart", 0.0))

    @property
    def x_increment(self) -> float:
        return float(self._metadata.get("XIncrement", 1.0))

    @property
    def x_values(self) -> np.ndarray[Any, np.dtype[np.floating[Any]]]:
        """Computed x-axis values: x_start + i * x_increment."""
        return np.arange(self.num_points, dtype=np.float64) * self.x_increment + self.x_start


class FloatImage2D(Measurement):
    """2D float image — shape (height, width), dtype float32."""

    @property
    def pixel_height(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[0]

    @property
    def pixel_width(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[1]

    @property
    def image_width_um(self) -> float:
        return float(self._metadata.get("ImageWidth", 0.0))

    @property
    def image_height_um(self) -> float:
        return float(self._metadata.get("ImageHeight", 0.0))


class ByteImage2D(Measurement):
    """2D byte image — shape (height, width, bpp), dtype uint8."""

    @property
    def pixel_height(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[0]

    @property
    def pixel_width(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[1]

    @property
    def bytes_per_pixel(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[2]

    @property
    def pixel_format(self) -> PixelFormat | str:
        raw: Any = self._metadata.get("PixelFormat", "")
        try:
            return PixelFormat[raw]
        except KeyError:
            return str(raw)

    @property
    def image_width_um(self) -> float:
        return float(self._metadata.get("ImageWidth", 0.0))

    @property
    def image_height_um(self) -> float:
        return float(self._metadata.get("ImageHeight", 0.0))


class FloatHypercube3D(Measurement):
    """3D float hypercube — shape (points, height, width), dtype float32."""

    @property
    def num_points(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[0]

    @property
    def pixel_height(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[1]

    @property
    def pixel_width(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[2]

    @property
    def image_width_um(self) -> float:
        return float(self._metadata.get("ImageWidth", 0.0))

    @property
    def image_height_um(self) -> float:
        return float(self._metadata.get("ImageHeight", 0.0))

    @property
    def x_start(self) -> float:
        return float(self._metadata.get("XStart", 0.0))

    @property
    def x_increment(self) -> float:
        return float(self._metadata.get("XIncrement", 1.0))

    @property
    def x_values(self) -> np.ndarray[Any, np.dtype[np.floating[Any]]]:
        """Computed x-axis values: x_start + i * x_increment."""
        return np.arange(self.num_points, dtype=np.float64) * self.x_increment + self.x_start

    def read_spectrum(self, x: int, y: int) -> np.ndarray[Any, Any]:
        """Extract spectrum at pixel (x, y). Returns shape (num_points,)."""
        return self.data[:, y, x]

    def read_image(self, index: int) -> np.ndarray[Any, Any]:
        """Extract image at spectral index. Returns shape (height, width)."""
        return self.data[index, :, :]


class ByteImageStack3D(Measurement):
    """3D byte image stack — shape (images, height, width, bpp), dtype uint8."""

    @property
    def num_images(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[0]

    @property
    def pixel_height(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[1]

    @property
    def pixel_width(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[2]

    @property
    def bytes_per_pixel(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[3]

    @property
    def pixel_format(self) -> PixelFormat | str:
        raw: Any = self._metadata.get("PixelFormat", "")
        try:
            return PixelFormat[raw]
        except KeyError:
            return str(raw)

    @property
    def image_width_um(self) -> float:
        return float(self._metadata.get("ImageWidth", 0.0))

    @property
    def image_height_um(self) -> float:
        return float(self._metadata.get("ImageHeight", 0.0))

    def read_image(self, index: int) -> np.ndarray[Any, Any]:
        """Extract image at stack index. Returns shape (height, width, bpp)."""
        return self.data[index, :, :, :]


# ---------------------------------------------------------------------------
# Concrete type classes (16 types)
# ---------------------------------------------------------------------------

# Spectra (FloatSpectrum1D)
class OPTIRSpectrum(FloatSpectrum1D): ...
class RamanSpectrum(FloatSpectrum1D): ...
class GeneratedSpectrum(FloatSpectrum1D): ...
class PTSRSSpectrum(FloatSpectrum1D): ...

# Float images (FloatImage2D)
class OPTIRImage(FloatImage2D): ...
class GeneratedImage(FloatImage2D): ...
class PTSRSImage(FloatImage2D): ...

# Byte images (ByteImage2D)
class CameraImage(ByteImage2D): ...
class FluorescenceImage(ByteImage2D): ...
class FLPTIRImage(ByteImage2D): ...

# Float hypercubes (FloatHypercube3D)
class OPTIRHyperspectra(FloatHypercube3D): ...
class RamanHyperspectra(FloatHypercube3D): ...
class OPTIRImageStack(FloatHypercube3D): ...
class PTSRSImageStack(FloatHypercube3D): ...

# Byte image stacks (ByteImageStack3D)
class CameraImageStack(ByteImageStack3D): ...
class FLPTIRImageStack(ByteImageStack3D): ...


# ---------------------------------------------------------------------------
# Type dispatch table
# ---------------------------------------------------------------------------

_TYPE_TO_CLASS: dict[str, type[Measurement]] = {
    "OPTIRSpectrum": OPTIRSpectrum,
    "RamanSpectrum": RamanSpectrum,
    "GeneratedSpectrum": GeneratedSpectrum,
    "PTSRSSpectrum": PTSRSSpectrum,
    "OPTIRImage": OPTIRImage,
    "GeneratedImage": GeneratedImage,
    "PTSRSImage": PTSRSImage,
    "CameraImage": CameraImage,
    "FluorescenceImage": FluorescenceImage,
    "FLPTIRImage": FLPTIRImage,
    "OPTIRHyperspectra": OPTIRHyperspectra,
    "RamanHyperspectra": RamanHyperspectra,
    "OPTIRImageStack": OPTIRImageStack,
    "CameraImageStack": CameraImageStack,
    "FLPTIRImageStack": FLPTIRImageStack,
    "PTSRSImageStack": PTSRSImageStack,
}

def _infer_shape(ndim: int, dtype: np.dtype[Any]) -> DataShape | None:
    """Infer DataShape from dataset rank and dtype for unknown types."""
    is_float = np.issubdtype(dtype, np.floating)
    is_int = np.issubdtype(dtype, np.integer)
    if ndim == 1 and is_float:
        return DataShape.FLOAT_SPECTRUM_1D
    if ndim == 2 and is_float:
        return DataShape.FLOAT_IMAGE_2D
    if ndim == 3 and is_int:
        return DataShape.BYTE_IMAGE_2D
    if ndim == 3 and is_float:
        return DataShape.FLOAT_HYPERCUBE_3D
    if ndim == 4 and is_int:
        return DataShape.BYTE_IMAGE_STACK_3D
    return None


def build_measurement(
    reader: HDF5Reader,
    hdf5_path: str,
    guid: str,
) -> Measurement:
    """Construct a typed Measurement from an HDF5 group path."""
    type_str = reader.read_type(hdf5_path)
    metadata = reader.build_metadata_view(hdf5_path)

    # Determine class and shape
    cls: type[Measurement]
    if type_str in _TYPE_TO_CLASS:
        cls = _TYPE_TO_CLASS[type_str]
        mt = MeasurementType(type_str)
        shape = TYPE_TO_SHAPE[mt]
    else:
        # Unknown type — keep base Measurement and infer shape if possible.
        cls = Measurement
        data_path = f"{hdf5_path}/DATA"
        if reader.has_dataset(data_path):
            ds_shape = reader.dataset_shape(data_path)
            ds_dtype = reader.dataset_dtype(data_path)
            inferred_shape = _infer_shape(len(ds_shape), ds_dtype)
            shape = inferred_shape or DataShape.FLOAT_SPECTRUM_1D
        else:
            shape = DataShape.FLOAT_SPECTRUM_1D
        mt = type_str  # type: ignore[assignment]

    # Build GENERATED children
    generated_guids = reader.list_generated_guids(hdf5_path)
    generated: tuple[Measurement, ...] = ()
    if generated_guids:
        gen_list: list[Measurement] = []
        for gen_guid in generated_guids:
            gen_path = f"{hdf5_path}/GENERATED/{gen_guid}"
            gen_list.append(build_measurement(reader, gen_path, gen_guid))
        generated = tuple(gen_list)

    return cls(
        guid=guid,
        measurement_type=mt,
        data_shape=shape,
        hdf5_path=hdf5_path,
        reader=reader,
        metadata=metadata,
        generated=generated,
    )
