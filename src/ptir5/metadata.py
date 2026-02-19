"""MetadataView — dict-like read-only access to HDF5 group attributes."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

import numpy as np


def _convert_value(val: Any) -> Any:
    """Convert an HDF5 attribute value to a Python-native type."""
    if isinstance(val, bytes):
        return val.decode("utf-8")
    if isinstance(val, np.bytes_):
        return bytes(val).decode("utf-8")
    if isinstance(val, np.generic):
        return val.item()
    if isinstance(val, np.ndarray):
        if val.ndim == 0:
            return val.item()
        if val.shape == (1,):
            return val[0].item()
        return val.tolist()
    return val


class MetadataView(Mapping[str, Any]):
    """Read-only, dict-like view over HDF5 group attributes.

    Merges attributes from the group itself and any sub-groups
    (Channel, ParticleData, ROIData) into a flat namespace.
    Values are converted to Python-native types on first access.
    """

    __slots__ = ("_cache", "_load")

    def __init__(self, load: Any) -> None:
        self._load = load
        self._cache: dict[str, Any] | None = None

    def _ensure_loaded(self) -> dict[str, Any]:
        if self._cache is None:
            self._cache = self._load()
        return self._cache

    def __getitem__(self, key: str) -> Any:
        return self._ensure_loaded()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._ensure_loaded())

    def __len__(self) -> int:
        return len(self._ensure_loaded())

    def __contains__(self, key: object) -> bool:
        return key in self._ensure_loaded()

    def __repr__(self) -> str:
        return f"MetadataView({dict(self._ensure_loaded())})"
