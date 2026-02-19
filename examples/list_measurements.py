"""List all measurements across multiple PTIR5 fixture files."""

from pathlib import Path

import ptir5

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
