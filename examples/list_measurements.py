"""List all measurements across multiple PTIR5 fixture files."""

import sys
from pathlib import Path

import ptir5

# Labels can contain non-ASCII text (e.g. superscript units). Write UTF-8 so that
# output redirected on Windows, which defaults to a legacy code page, still works.
sys.stdout.reconfigure(encoding="utf-8")

fixtures = Path("tests/fixtures")
for path in sorted(fixtures.glob("*.ptir")):
    with ptir5.open(path) as f:
        print(f"\n{path.name}:")
        print(f"  Measurements: {len(f.measurements)}")
        for m in f.measurements:
            print(f"    {type(m).__name__}: {m.label!r} {m.data.shape} {m.data.dtype}")
            for g in m.generated:
                print(f"      -> {type(g).__name__}: {g.label!r} {g.data.shape}")
        print(f"  Backgrounds: {len(f.backgrounds)}")
        for bg in f.backgrounds:
            print(f"    {type(bg).__name__}: {bg.label!r} {bg.data.shape}")
        print(f"  Has tree: {f.has_tree}")
