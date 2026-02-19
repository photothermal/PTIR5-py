"""PTIR5File — main entry point for reading PTIR5 files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ptir5._reader import HDF5Reader
from ptir5.exceptions import FileClosedError, MeasurementNotFoundError
from ptir5.models import Measurement, build_measurement
from ptir5.tree import TreeFolder, TreeLeaf, TreeRoot

if TYPE_CHECKING:
    from pathlib import Path

    from ptir5.enums import MeasurementType


class PTIR5File:
    """Read-only accessor for a PTIR5 (.ptir) file.

    Use as a context manager::

        with ptir5.open("sample.ptir") as f:
            for m in f.measurements:
                print(m.label, m.measurement_type)
    """

    __slots__ = (
        "_path",
        "_reader",
        "_measurements",
        "_backgrounds",
        "_measurement_map",
        "_background_map",
        "_tree",
        "_tree_loaded",
    )

    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        self._reader = HDF5Reader(path)
        self._measurements: tuple[Measurement, ...] | None = None
        self._backgrounds: tuple[Measurement, ...] | None = None
        self._measurement_map: dict[str, Measurement] | None = None
        self._background_map: dict[str, Measurement] | None = None
        self._tree: TreeRoot | None = None
        self._tree_loaded = False

    def _check_open(self) -> None:
        if not self._reader.is_open:
            raise FileClosedError("PTIR5 file is closed")

    # -- Properties ---------------------------------------------------------

    @property
    def path(self) -> str:
        return self._path

    @property
    def is_open(self) -> bool:
        return self._reader.is_open

    @property
    def measurements(self) -> tuple[Measurement, ...]:
        self._check_open()
        if self._measurements is None:
            self._load_measurements()
        assert self._measurements is not None
        return self._measurements

    @property
    def backgrounds(self) -> tuple[Measurement, ...]:
        self._check_open()
        if self._backgrounds is None:
            self._load_backgrounds()
        assert self._backgrounds is not None
        return self._backgrounds

    @property
    def has_tree(self) -> bool:
        self._check_open()
        return self._reader.has_tree()

    @property
    def tree(self) -> TreeRoot | None:
        self._check_open()
        if not self._tree_loaded:
            self._load_tree()
        return self._tree

    # -- Lookup methods -----------------------------------------------------

    def get_measurement(self, guid: str) -> Measurement:
        self._check_open()
        if self._measurement_map is None:
            self._load_measurements()
        assert self._measurement_map is not None
        try:
            return self._measurement_map[guid]
        except KeyError:
            raise MeasurementNotFoundError(guid) from None

    def get_background(self, guid: str) -> Measurement:
        self._check_open()
        if self._background_map is None:
            self._load_backgrounds()
        assert self._background_map is not None
        try:
            return self._background_map[guid]
        except KeyError:
            raise MeasurementNotFoundError(guid) from None

    def measurements_by_type(
        self, type_: MeasurementType
    ) -> tuple[Measurement, ...]:
        return tuple(m for m in self.measurements if m.measurement_type == type_)

    # -- Lifecycle ----------------------------------------------------------

    def close(self) -> None:
        self._reader.close()

    def __enter__(self) -> PTIR5File:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        state = "open" if self.is_open else "closed"
        return f"<PTIR5File {self._path!r} ({state})>"

    # -- Internal loading ---------------------------------------------------

    def _load_measurements(self) -> None:
        guids = self._reader.list_measurement_guids()
        items: list[Measurement] = []
        mapping: dict[str, Measurement] = {}
        for guid in guids:
            path = f"MEASUREMENTS/{guid}"
            m = build_measurement(self._reader, path, guid)
            items.append(m)
            mapping[guid] = m
        self._measurements = tuple(items)
        self._measurement_map = mapping

    def _load_backgrounds(self) -> None:
        guids = self._reader.list_background_guids()
        items: list[Measurement] = []
        mapping: dict[str, Measurement] = {}
        for guid in guids:
            path = f"BACKGROUNDS/{guid}"
            m = build_measurement(self._reader, path, guid)
            items.append(m)
            mapping[guid] = m
        self._backgrounds = tuple(items)
        self._background_map = mapping

    def _load_tree(self) -> None:
        self._tree_loaded = True
        if not self._reader.has_tree():
            self._tree = None
            return

        # Ensure measurements are loaded for GUID resolution
        if self._measurement_map is None:
            self._load_measurements()
        assert self._measurement_map is not None

        # Build lookup of TREE node info
        root_child_ids = self._reader.read_tree_node_ids("TREE")
        children = tuple(self._build_tree_node(guid) for guid in root_child_ids)
        self._tree = TreeRoot(children)

    def _build_tree_node(self, guid: str) -> TreeFolder | TreeLeaf:
        tree_path = f"TREE/{guid}"
        type_str = self._reader.read_type(tree_path)
        label = self._reader.read_label(tree_path)

        if type_str == "FOLDER":
            child_ids = self._reader.read_tree_node_ids(tree_path)
            children = tuple(self._build_tree_node(cid) for cid in child_ids)
            return TreeFolder(name=label, children=children)
        else:
            assert self._measurement_map is not None
            measurement = self._measurement_map.get(guid)
            return TreeLeaf(name=label, guid=guid, measurement=measurement)
