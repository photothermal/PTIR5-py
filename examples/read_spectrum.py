"""Read and display an O-PTIR spectrum from a PTIR5 file."""

import ptir5

with ptir5.open("tests/fixtures/sample_optir_spectrum.ptir") as f:
    spec = f.measurements[0]
    assert isinstance(spec, ptir5.OPTIRSpectrum)

    print(f"Label:      {spec.label}")
    print(f"Points:     {spec.num_points}")
    print(f"X start:    {spec.x_start}")
    print(f"X inc:      {spec.x_increment}")
    print(f"X units:    {spec.metadata.get('XUnits', '')}")
    print(f"X range:    {spec.x_values[0]:.1f} - {spec.x_values[-1]:.1f}")
    print(f"Data shape: {spec.data.shape}")
    print(f"Data dtype: {spec.data.dtype}")
    print(f"Min value:  {spec.data.min():.4f}")
    print(f"Max value:  {spec.data.max():.4f}")
