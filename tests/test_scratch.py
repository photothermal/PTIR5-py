"""Scratch marker: uncommitted batch outputs (PSC.PTIR5.SDK ``DataObject.IsScratch``).

PTIR Studio deletes scratch objects the tree cannot reach when it opens a file;
a read-only reader still lists them but flags them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

import ptir5

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    WritePtir = Callable[..., Path]


@pytest.mark.parametrize(("attrs", "expected"), [
    ({}, False), ({"Scratch": ""}, False), ({"Scratch": "ratio-preview-1"}, True),
])
def test_scratch_marker_is_reported_not_filtered(
    write_ptir: WritePtir, attrs: dict[str, object], expected: bool
) -> None:
    with ptir5.open(write_ptir("OPTIRImage", np.zeros((2, 2), np.float32), attrs=attrs)) as f:
        (m,) = f.measurements
        assert m.is_scratch is expected
