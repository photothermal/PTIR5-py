"""Browse the document tree of a PTIR5 file."""

import ptir5

with ptir5.open("tests/fixtures/sample_optir_image_stack.ptir") as f:
    if f.tree is None:
        print("No tree in this file")
    else:
        print("Document Tree:")
        for node, folders, leaves in f.tree.walk():
            name = getattr(node, "name", "ROOT")
            print(f"\n  [{name}]")
            for folder in folders:
                print(f"    [Folder] {folder.name}")
            for leaf in leaves:
                m = leaf.measurement
                if m:
                    print(f"    {leaf.name}: {m.measurement_type} {m.data.shape}")
                else:
                    print(f"    {leaf.name}: (no measurement)")
