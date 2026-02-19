"""Read and display an O-PTIR image from a PTIR5 file."""

import ptir5

with ptir5.open("tests/fixtures/sample_optir_image.ptir") as f:
    img = f.measurements[0]
    assert isinstance(img, ptir5.OPTIRImage)

    print(f"Label:        {img.label}")
    print(f"Pixels:       {img.pixel_width} x {img.pixel_height}")
    print(f"Physical:     {img.image_width_um:.1f} x {img.image_height_um:.1f} um")
    print(f"Data shape:   {img.data.shape}")
    print(f"Data dtype:   {img.data.dtype}")
    print(f"Wavenumber:   {img.metadata.get('Wavenumber', 'N/A')} cm-1")
    print(f"Min value:    {img.data.min():.6f}")
    print(f"Max value:    {img.data.max():.6f}")
