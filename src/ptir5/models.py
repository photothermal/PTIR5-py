"""Data model classes for PTIR5 measurements.

Hierarchy:
    Measurement (base)
    ├── FloatSpectrum1D    — 1D float spectra
    ├── FloatImage2D       — 2D float images (OPTIR, Generated, PTSRS)
    ├── ByteImage2D        — 2D byte images (Camera, Fluorescence, FLPTIR)
    ├── FloatHypercube3D   — 3D float cubes (OPTIRImageStack, PTSRSImageStack)
    │   └── HyperspectralCube — spectral and time-domain cubes (one spectrum per pixel)
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

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import numpy as np

from ptir5.enums import TYPE_TO_SHAPE, DataShape, MeasurementType, PixelFormat
from ptir5.exceptions import InvalidMeasurementError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ptir5._reader import HDF5Reader
    from ptir5.metadata import MetadataView


def _resolve_pixel_format(metadata: MetadataView) -> PixelFormat | str:
    """Map the ``PixelFormat`` attribute to the enum, keeping unknown names as strings."""
    raw: Any = metadata.get("PixelFormat", "")
    try:
        return PixelFormat[raw]
    except KeyError:
        return str(raw)


class AuxiliaryDatasets(Mapping[str, np.ndarray[Any, Any]]):
    """Read-only mapping of the side datasets stored next to a measurement's DATA.

    Keys are the sibling dataset names (``Wavenumber``, ``NumAverages``,
    ``ComponentCompletion``, ...), excluding ``DATA``. The name list is read
    once; each value is read from the file on every access and never cached.
    """

    __slots__ = ("_names", "_path", "_reader")

    def __init__(self, reader: HDF5Reader, hdf5_path: str) -> None:
        self._reader = reader
        self._path = hdf5_path
        self._names: tuple[str, ...] | None = None

    def _ensure_names(self) -> tuple[str, ...]:
        if self._names is None:
            self._names = tuple(
                name for name in self._reader.list_datasets(self._path) if name != "DATA"
            )
        return self._names

    def __getitem__(self, key: str) -> np.ndarray[Any, Any]:
        if key not in self._ensure_names():
            raise KeyError(key)
        return self._reader.read_dataset(f"{self._path}/{key}")

    def __iter__(self) -> Iterator[str]:
        return iter(self._ensure_names())

    def __len__(self) -> int:
        return len(self._ensure_names())

    def __contains__(self, key: object) -> bool:
        return key in self._ensure_names()

    def __repr__(self) -> str:
        return f"AuxiliaryDatasets({list(self._ensure_names())})"


def _read_component_completion(
    reader: HDF5Reader, hdf5_path: str, expected_shape: tuple[int, ...]
) -> np.ndarray[Any, np.dtype[np.bool_]] | None:
    """Decode the opt-in ``ComponentCompletion`` marker (spec §7.4.1).

    Absent means completion is unknown (``None``). Only the value 1 reads as
    complete; 0 and any corrupt value read as incomplete (fail closed).
    """
    path = f"{hdf5_path}/ComponentCompletion"
    if not reader.has_dataset(path):
        return None
    dtype = reader.dataset_dtype(path)
    shape = reader.dataset_shape(path)
    if dtype != np.uint8 or shape != expected_shape:
        raise InvalidMeasurementError(
            f"ComponentCompletion must be uint8 with shape {expected_shape}; "
            f"got shape {shape} dtype {dtype} at {hdf5_path}"
        )
    result: np.ndarray[Any, np.dtype[np.bool_]] = reader.read_dataset(path) == 1
    return result


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

    @property
    def auxiliary(self) -> AuxiliaryDatasets:
        """Side datasets stored next to DATA (per-pixel or per-frame arrays)."""
        return AuxiliaryDatasets(self._reader, self._hdf5_path)

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
        return _resolve_pixel_format(self._metadata)

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

    @property
    def component_completion(self) -> np.ndarray[Any, np.dtype[np.bool_]] | None:
        """Per-component completion, or ``None`` when the file does not track it.

        Cubes track one flag per pixel ``(height, width)``; float image stacks
        one flag per frame. ``False`` means incomplete or corrupt.
        """
        return _read_component_completion(
            self._reader, self._hdf5_path, self._completion_shape()
        )

    def _completion_shape(self) -> tuple[int, ...]:
        return (self.pixel_height, self.pixel_width)


class HyperspectralCube(FloatHypercube3D):
    """A cube holding one spectrum (or time-domain waveform) per X/Y pixel.

    Base for :class:`OPTIRHyperspectra`, :class:`RamanHyperspectra` and
    :class:`TimeDomainCube`, mirroring the C# SDK's ``HyperspectralArrayData``.
    Image stacks (:class:`OPTIRImageStack`, :class:`PTSRSImageStack`) share the
    ``(points, height, width)`` storage but are not hyperspectral cubes.
    """


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
    def component_completion(self) -> np.ndarray[Any, np.dtype[np.bool_]] | None:
        """Per-frame completion ``(num_images,)``, or ``None`` when untracked.

        ``False`` means incomplete or corrupt.
        """
        return _read_component_completion(self._reader, self._hdf5_path, (self.num_images,))

    @property
    def pixel_height(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[1]

    @property
    def pixel_width(self) -> int:
        return self._reader.dataset_shape(f"{self._hdf5_path}/DATA")[2]

    @property
    def pixel_format(self) -> PixelFormat | str:
        return _resolve_pixel_format(self._metadata)

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
# Concrete type classes (18 types)
# ---------------------------------------------------------------------------

# Spectra (FloatSpectrum1D)
class OPTIRSpectrum(FloatSpectrum1D): ...
class RamanSpectrum(FloatSpectrum1D): ...
class GeneratedSpectrum(FloatSpectrum1D): ...
class PTSRSSpectrum(FloatSpectrum1D): ...
class TimeDomainBurst(FloatSpectrum1D):
    """A waveform captured at one X/Y location; the x-axis is time (µs), not wavenumber."""

# Float images (FloatImage2D)
class OPTIRImage(FloatImage2D): ...
class GeneratedImage(FloatImage2D): ...
class PTSRSImage(FloatImage2D): ...

# Byte images (ByteImage2D); FLPTIRImage is dual-format, see below
class CameraImage(ByteImage2D): ...
class FluorescenceImage(ByteImage2D): ...

# Hyperspectral cubes (HyperspectralCube)
class OPTIRHyperspectra(HyperspectralCube): ...
class RamanHyperspectra(HyperspectralCube): ...
class TimeDomainCube(HyperspectralCube):
    """One time-domain waveform per X/Y pixel; the leading axis is time (µs)."""

# Float image stacks stored as (images, height, width) float32 (FloatHypercube3D);
# their components are frames, so completion is tracked per frame.
class OPTIRImageStack(FloatHypercube3D):
    def _completion_shape(self) -> tuple[int, ...]:
        return (self.num_points,)


class PTSRSImageStack(FloatHypercube3D):
    def _completion_shape(self) -> tuple[int, ...]:
        return (self.num_points,)

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
            f"FL-PTIR legacy DATA must be uint8 with trailing dim 4; "
            f"got shape {raw.shape} dtype {raw.dtype} at {hdf5_path}"
        )
    return (
        np.ascontiguousarray(raw).view(np.float32).reshape(raw.shape[:-1])
    )


# Rank-2 FLPTIRImage dtypes the SDK accepts: Gray32Float, Gray16 and Gray8.
_FLPTIR_IMAGE_RANK2_DTYPES = frozenset({np.dtype(np.float32), np.dtype(np.uint16),
                                        np.dtype(np.uint8)})


class FLPTIRImage:
    """Marker mixin for single widefield FL-PTIR images.

    FLPTIRImage has two on-disk formats (matching the C# PSC.PTIR5.SDK):

    - **Rank-2 format**: ``(height, width)`` float32 (``Gray32Float``), uint16
      (``Gray16``) or uint8 (``Gray8``); the dataset dtype decides. Current
      writers emit this layout. Represented by :class:`_Rank2FLPTIRImage`,
      which also inherits from :class:`FloatImage2D`.
    - **Legacy rank-3 byte format**: ``(height, width, 4)`` uint8 where each
      4-byte pixel is the byte representation of a float32 value. Represented
      by :class:`_LegacyFLPTIRImage`, which also inherits from
      :class:`ByteImage2D`.

    Regardless of the format, :attr:`data_float32` returns ``(height, width)``
    float32 imagery. The raw on-disk dataset stays available via ``data``.
    """

    is_legacy: bool
    _metadata: MetadataView

    @property
    def data_float32(self) -> np.ndarray[Any, np.dtype[np.float32]]:
        """The image as ``(height, width)`` float32."""
        raise NotImplementedError

    @property
    def pixel_format(self) -> PixelFormat | str:
        return _resolve_pixel_format(self._metadata)


class _LegacyFLPTIRImage(FLPTIRImage, ByteImage2D):
    """Legacy rank-3 uint8 FLPTIRImage. ``data`` returns raw bytes;
    ``data_float32`` returns canonical float32 imagery."""

    is_legacy = True

    @property
    def data_float32(self) -> np.ndarray[Any, np.dtype[np.float32]]:
        raw = self._reader.read_dataset(f"{self._hdf5_path}/DATA")
        return _reinterpret_legacy_flptir_bytes(raw, self._hdf5_path)


class _Rank2FLPTIRImage(FLPTIRImage, FloatImage2D):
    """Rank-2 FLPTIRImage. ``data`` returns the stored float32, uint16 or
    uint8 pixels; ``data_float32`` converts them to float32."""

    is_legacy = False

    @property
    def data_float32(self) -> np.ndarray[Any, np.dtype[np.float32]]:
        raw = self._reader.read_dataset(f"{self._hdf5_path}/DATA")
        return raw.astype(np.float32, copy=False)


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
    # FLPTIRImage and FLPTIRImageStack are rank-dispatched in build_measurement,
    # not via this table, because their concrete class depends on the on-disk
    # dataset shape.
    "OPTIRHyperspectra": OPTIRHyperspectra,
    "RamanHyperspectra": RamanHyperspectra,
    "OPTIRImageStack": OPTIRImageStack,
    "CameraImageStack": CameraImageStack,
    "PTSRSImageStack": PTSRSImageStack,
    "TimeDomainBurst": TimeDomainBurst,
    "TimeDomainCube": TimeDomainCube,
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


def _flptir_image_class(
    reader: HDF5Reader, hdf5_path: str
) -> tuple[type[Measurement], DataShape]:
    """Pick the FLPTIRImage class from the dataset rank and dtype.

    Matches the C# SDK's ``FLPTIRImage.Open``: rank 3 is the legacy float-bytes
    layout (validated when read); rank 2 must be float32, uint16 or uint8.
    """
    data_path = f"{hdf5_path}/DATA"
    if not reader.has_dataset(data_path):
        raise InvalidMeasurementError(f"FLPTIRImage is missing DATA dataset at {hdf5_path}")
    ds_rank = len(reader.dataset_shape(data_path))
    if ds_rank == 3:
        return _LegacyFLPTIRImage, DataShape.BYTE_IMAGE_2D
    if ds_rank == 2:
        ds_dtype = reader.dataset_dtype(data_path)
        if ds_dtype not in _FLPTIR_IMAGE_RANK2_DTYPES:
            raise InvalidMeasurementError(
                f"FLPTIRImage rank-2 DATA must be float32, uint16 or uint8; got dtype "
                f"{ds_dtype} at {hdf5_path}"
            )
        return _Rank2FLPTIRImage, DataShape.FLOAT_IMAGE_2D
    raise InvalidMeasurementError(
        f"FLPTIRImage DATA must be rank 2 or 3; found rank {ds_rank} at {hdf5_path}"
    )


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
    if type_str == "FLPTIRImage":
        mt = MeasurementType.FLPTIRImage
        cls, shape = _flptir_image_class(reader, hdf5_path)
    elif type_str == "FLPTIRImageStack":
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
