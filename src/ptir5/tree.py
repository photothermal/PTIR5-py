"""Tree navigation for PTIR5 hierarchical document structure."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ptir5.models import Measurement


class TreeLeaf:
    """A leaf node in the PTIR5 tree, representing a measurement."""

    __slots__ = ("_name", "_guid", "_measurement")

    def __init__(self, name: str, guid: str, measurement: Measurement | None) -> None:
        self._name = name
        self._guid = guid
        self._measurement = measurement

    @property
    def name(self) -> str:
        return self._name

    @property
    def guid(self) -> str:
        return self._guid

    @property
    def measurement(self) -> Measurement | None:
        return self._measurement

    def __repr__(self) -> str:
        return f"TreeLeaf({self._name!r}, guid={self._guid!r})"


class TreeFolder:
    """A folder node in the PTIR5 tree, containing children."""

    __slots__ = ("_name", "_children")

    def __init__(self, name: str, children: tuple[TreeFolder | TreeLeaf, ...]) -> None:
        self._name = name
        self._children = children

    @property
    def name(self) -> str:
        return self._name

    @property
    def children(self) -> tuple[TreeFolder | TreeLeaf, ...]:
        return self._children

    @property
    def folders(self) -> tuple[TreeFolder, ...]:
        return tuple(c for c in self._children if isinstance(c, TreeFolder))

    @property
    def leaves(self) -> tuple[TreeLeaf, ...]:
        return tuple(c for c in self._children if isinstance(c, TreeLeaf))

    def walk(self) -> Iterator[tuple[TreeFolder, tuple[TreeFolder, ...], tuple[TreeLeaf, ...]]]:
        """Walk the tree top-down, yielding (folder, sub_folders, leaves)."""
        yield self, self.folders, self.leaves
        for f in self.folders:
            yield from f.walk()

    def __repr__(self) -> str:
        return f"TreeFolder({self._name!r}, children={len(self._children)})"


class TreeRoot:
    """The root of the PTIR5 document tree."""

    __slots__ = ("_children",)

    def __init__(self, children: tuple[TreeFolder | TreeLeaf, ...]) -> None:
        self._children = children

    @property
    def children(self) -> tuple[TreeFolder | TreeLeaf, ...]:
        return self._children

    @property
    def folders(self) -> tuple[TreeFolder, ...]:
        return tuple(c for c in self._children if isinstance(c, TreeFolder))

    @property
    def leaves(self) -> tuple[TreeLeaf, ...]:
        return tuple(c for c in self._children if isinstance(c, TreeLeaf))

    _WalkItem = tuple[
        "TreeFolder | TreeRoot", tuple["TreeFolder", ...], tuple[TreeLeaf, ...]
    ]

    def walk(self) -> Iterator[_WalkItem]:
        """Walk the tree top-down, yielding (node, sub_folders, leaves)."""
        yield self, self.folders, self.leaves
        for f in self.folders:
            yield from f.walk()

    def __repr__(self) -> str:
        return f"TreeRoot(children={len(self._children)})"
