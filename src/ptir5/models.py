"""Data model classes for PTIR5 measurements.

Hierarchy:
    Measurement (base)
    ├── FloatSpectrum1D    — 1D float spectra
    ├── FloatImage2D       — 2D float images (OPTIR, Generated, PTSRS)
    ├── ByteImage2D        — 2D byte images (Camera, Fluorescence, FLPTIR)
    ├── FloatHypercube3D   — 3D float cubes (Hyperspectra, OPTIRImageStack)
    └── ImageStack3D       — abstract base for stacks of 2D images
        ├── ByteImageStack3D   — rank-4 uint8 (CameraImageStack, legacy FLPTIRImageStack)
        └── FloatImageStack3D  — rank-3 float32 (rank-3 FLPTIRImageStack)

The ``FLPTIRImageStack`` mixin marks both legacy and rank-3 concrete classes,
so callers can dispatch on either the storage shape (``ByteImageStack3D`` /
``FloatImageStack3D``), the abstract stack contract (``ImageStack3D``), or the
measurement type (``FLPTIRImageStack``).

Each base shape has concrete subclasses for each MeasurementType.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from ptir5.enums import TYPE_TO_SHAPE, DataShape, MeasurementType, PixelFormat
from ptir5.exceptions import InvalidMeasurementError

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
        return self._reader.read_dataset_slice(
            f"{self._hdf5_path}/DATA", (slice(None), y, x)
        )

    def read_image(self, index: int) -> np.ndarray[Any, Any]:
        """Extract image at spectral index. Returns shape (height, width)."""
        return self._reader.read_dataset_slice(
            f"{self._hdf5_path}/DATA", (index, slice(None), slice(None))
        )


class ImageStack3D(Measurement):
    """Abstract base for a stack of 2D images.

    Concrete subclasses are :class:`ByteImageStack3D` (rank-4 uint8 storage)
    and :class:`FloatImageStack3D` (rank-3 float32 storage). Distinct from
    :class:`FloatHypercube3D`, whose first axis is spectral rather than a
    frame index.

    The :meth:`read_image` return type and shape differ between subclasses;
    use the concrete-class API when shape/dtype matter.
    """

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


class ByteImageStack3D(ImageStack3D):
    """3D byte image stack — shape (images, height, width, bpp), dtype uint8."""

    @property
    def bytes_per_pixel(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[3]

    def read_image(self, index: int) -> np.ndarray[Any, Any]:
        """Extract image at stack index. Returns shape (height, width, bpp)."""
        return self._reader.read_dataset_slice(
            f"{self._hdf5_path}/DATA",
            (index, slice(None), slice(None), slice(None)),
        )


class FloatImageStack3D(ImageStack3D):
    """3D float image stack — shape (images, height, width), dtype float32."""

    def read_image(self, index: int) -> np.ndarray[Any, np.dtype[np.float32]]:
        """Extract image at stack index. Returns shape (height, width) float32."""
        result = self._reader.read_dataset_slice(
            f"{self._hdf5_path}/DATA",
            (index, slice(None), slice(None)),
        )
        return result


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


def _reinterpret_legacy_flptir_bytes(
    raw: np.ndarray[Any, Any], hdf5_path: str
) -> np.ndarray[Any, np.dtype[np.float32]]:
    """Validate the legacy rank-4 layout and reinterpret bytes as float32.

    The legacy on-disk layout is ``(..., 4) uint8`` where each contiguous
    4-byte tile is the byte representation of one float32 pixel. Any other
    shape/dtype combination indicates a malformed file.
    """
    if raw.dtype != np.uint8 or raw.ndim < 1 or raw.shape[-1] != 4:
        raise InvalidMeasurementError(
            f"FLPTIRImageStack legacy DATA must be uint8 with trailing dim 4; "
            f"got shape {raw.shape} dtype {raw.dtype} at {hdf5_path}"
        )
    return (
        np.ascontiguousarray(raw).view(np.float32).reshape(raw.shape[:-1])
    )


class FLPTIRImageStack:
    """Marker mixin for widefield FLPTIR image stacks.

    FLPTIRImageStack has two on-disk formats (matching the C# PSC.PTIR5.SDK):

    - **Legacy rank-4 byte format**: ``(num_images, height, width, 4)`` uint8.
      Each 4-byte pixel is the byte representation of a float32 value (the
      legacy storage was typed as bytes but always Gray32Float in practice).
      Represented by :class:`_LegacyFLPTIRImageStack`, which also inherits
      from :class:`ByteImageStack3D`.
    - **Rank-3 float format**: ``(num_images, height, width)`` float32. Newly
      allocated stacks use this layout. Represented by
      :class:`_FloatFLPTIRImageStack`, which also inherits from
      :class:`FloatImageStack3D`.

    Both concrete classes inherit from this mixin, so callers can use
    ``isinstance(m, FLPTIRImageStack)`` to dispatch by measurement type
    regardless of storage format. They can additionally use
    ``isinstance(m, ByteImageStack3D)`` / ``isinstance(m, FloatImageStack3D)``
    or the shared :class:`ImageStack3D` base to dispatch by storage shape.

    Regardless of the underlying format, :meth:`read_image` and
    :attr:`data_float32` return float32 imagery so callers can ignore the
    storage format. The raw on-disk dataset is always available via the
    :attr:`data` property.
    """

    # Concrete subclasses populate ``is_legacy`` and ``data_float32``.
    # ``read_image`` comes from the storage base (ByteImageStack3D for legacy,
    # FloatImageStack3D for the rank-3 format); the legacy concrete class
    # overrides it to reinterpret the bytes as float32.
    is_legacy: bool

    @property
    def data_float32(self) -> np.ndarray[Any, np.dtype[np.float32]]:
        """The full stack as ``(num_images, height, width)`` float32.

        Implementations: :class:`_LegacyFLPTIRImageStack` reinterprets the
        rank-4 byte storage; :class:`_FloatFLPTIRImageStack` returns the
        rank-3 dataset as written.
        """
        raise NotImplementedError


class _LegacyFLPTIRImageStack(FLPTIRImageStack, ByteImageStack3D):
    """Legacy rank-4 uint8 FLPTIRImageStack. ``data`` returns raw bytes;
    ``data_float32`` and ``read_image`` return canonical float32 imagery."""

    is_legacy = True

    @property
    def data_float32(self) -> np.ndarray[Any, np.dtype[np.float32]]:
        raw = self._reader.read_dataset(f"{self._hdf5_path}/DATA")
        return _reinterpret_legacy_flptir_bytes(raw, self._hdf5_path)

    def read_image(self, index: int) -> np.ndarray[Any, np.dtype[np.float32]]:
        raw = self._reader.read_dataset_slice(
            f"{self._hdf5_path}/DATA",
            (index, slice(None), slice(None), slice(None)),
        )
        return _reinterpret_legacy_flptir_bytes(raw, self._hdf5_path)


class _FloatFLPTIRImageStack(FLPTIRImageStack, FloatImageStack3D):
    """Rank-3 float32 FLPTIRImageStack — the format newly allocated stacks
    use. ``data``, ``data_float32``, and ``read_image`` all return float32.

    ``build_measurement`` validates that the dataset is float32 before
    constructing this class, so reads from a well-formed file are guaranteed
    to return float32. The defensive dtype checks on the read methods catch
    direct instantiation against a malformed dataset.
    """

    is_legacy = False

    def _check_float32_dtype(self, arr: np.ndarray[Any, Any]) -> None:
        if arr.dtype != np.float32:
            raise InvalidMeasurementError(
                f"FLPTIRImageStack rank-3 DATA must be float32; got dtype "
                f"{arr.dtype} at {self._hdf5_path}"
            )

    @property
    def data_float32(self) -> np.ndarray[Any, np.dtype[np.float32]]:
        result = self._reader.read_dataset(f"{self._hdf5_path}/DATA")
        self._check_float32_dtype(result)
        return result

    def read_image(self, index: int) -> np.ndarray[Any, np.dtype[np.float32]]:
        result = self._reader.read_dataset_slice(
            f"{self._hdf5_path}/DATA",
            (index, slice(None), slice(None)),
        )
        self._check_float32_dtype(result)
        return result


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
    # FLPTIRImageStack is rank-dispatched in build_measurement, not via this
    # table, because its concrete class depends on the on-disk dataset shape.
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
    if type_str == "FLPTIRImageStack":
        # FLPTIRImageStack has two on-disk formats — pick the concrete class
        # and matching DataShape from the actual dataset rank/dtype, and
        # reject anything that doesn't match one of the two valid layouts.
        mt = MeasurementType.FLPTIRImageStack
        data_path = f"{hdf5_path}/DATA"
        if not reader.has_dataset(data_path):
            raise InvalidMeasurementError(
                f"FLPTIRImageStack is missing DATA dataset at {hdf5_path}"
            )
        ds_rank = len(reader.dataset_shape(data_path))
        ds_dtype = reader.dataset_dtype(data_path)
        if ds_rank == 4:
            # Full legacy-layout validation (uint8 + trailing dim 4) happens
            # on first byte->float reinterpret in _reinterpret_legacy_flptir_bytes.
            cls = _LegacyFLPTIRImageStack
            shape = DataShape.BYTE_IMAGE_STACK_3D
        elif ds_rank == 3:
            if ds_dtype != np.float32:
                raise InvalidMeasurementError(
                    f"FLPTIRImageStack rank-3 DATA must be float32; got dtype "
                    f"{ds_dtype} at {hdf5_path}"
                )
            cls = _FloatFLPTIRImageStack
            shape = DataShape.FLOAT_IMAGE_STACK_3D
        else:
            raise InvalidMeasurementError(
                f"FLPTIRImageStack DATA must be rank 3 or 4; found rank "
                f"{ds_rank} at {hdf5_path}"
            )
    elif type_str in _TYPE_TO_CLASS:
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
