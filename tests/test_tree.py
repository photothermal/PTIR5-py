"""Tests for hierarchical tree navigation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ptir5
from ptir5 import TreeFolder, TreeLeaf, TreeRoot

if TYPE_CHECKING:
    from pathlib import Path


def test_has_tree(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        assert f.has_tree


def test_tree_root_type(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        tree = f.tree
        assert isinstance(tree, TreeRoot)


def test_optir_spectrum_tree_structure(optir_spectrum_path: Path) -> None:
    """sample_optir_spectrum: ROOT -> leaf (O-PTIR0 1)."""
    with ptir5.open(optir_spectrum_path) as f:
        tree = f.tree
        assert tree is not None
        assert len(tree.children) == 1
        leaf = tree.children[0]
        assert isinstance(leaf, TreeLeaf)
        assert leaf.name == "O-PTIR0 1"
        assert leaf.measurement is not None
        assert leaf.measurement is f.measurements[0]


def test_camera_image_tree_with_folder(camera_image_path: Path) -> None:
    """sample_camera_image: ROOT -> folder(Video Images) -> leaf(Camera 1)."""
    with ptir5.open(camera_image_path) as f:
        tree = f.tree
        assert tree is not None
        assert len(tree.children) == 1

        folder = tree.children[0]
        assert isinstance(folder, TreeFolder)
        assert folder.name == "Video Images"
        assert len(folder.children) == 1

        leaf = folder.children[0]
        assert isinstance(leaf, TreeLeaf)
        assert leaf.name == "Camera 1"
        assert leaf.measurement is not None
        assert leaf.guid == f.measurements[0].guid


def test_image_stack_tree_with_multiple_leaves(optir_image_stack_path: Path) -> None:
    """sample_optir_image_stack: ROOT -> folder -> 2 leaves."""
    with ptir5.open(optir_image_stack_path) as f:
        tree = f.tree
        assert tree is not None
        assert len(tree.children) == 1

        folder = tree.children[0]
        assert isinstance(folder, TreeFolder)
        assert len(folder.leaves) == 2


def test_tree_walk(camera_image_path: Path) -> None:
    with ptir5.open(camera_image_path) as f:
        tree = f.tree
        assert tree is not None
        nodes = list(tree.walk())
        # ROOT + 1 folder = 2 walk entries
        assert len(nodes) == 2
        # First is root
        node, folders, leaves = nodes[0]
        assert isinstance(node, TreeRoot)
        assert len(folders) == 1
        assert len(leaves) == 0
        # Second is folder
        node2, folders2, leaves2 = nodes[1]
        assert isinstance(node2, TreeFolder)
        assert len(leaves2) == 1


def test_folder_properties(camera_image_path: Path) -> None:
    with ptir5.open(camera_image_path) as f:
        tree = f.tree
        assert tree is not None
        assert len(tree.folders) == 1
        assert len(tree.leaves) == 0
        folder = tree.folders[0]
        assert len(folder.folders) == 0
        assert len(folder.leaves) == 1


def test_tree_repr(optir_spectrum_path: Path) -> None:
    with ptir5.open(optir_spectrum_path) as f:
        tree = f.tree
        assert tree is not None
        assert "TreeRoot" in repr(tree)
        leaf = tree.children[0]
        assert isinstance(leaf, TreeLeaf)
        assert "TreeLeaf" in repr(leaf)
