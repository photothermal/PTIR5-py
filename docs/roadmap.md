# ptir5 Roadmap

Forward-looking ideas for the library. Items here are aspirational, not
committed work. Open a GitHub issue to discuss or claim any of them; this
document is the lightweight inbox before something becomes a tracked issue.

## Selective read APIs

- Region-of-interest reads for images and hypercubes — load only the requested
  sub-rectangle instead of the full DATA dataset.
- Multi-point spectrum extraction from hyperspectral data — read N pixels'
  spectra in one HDF5 call rather than N round-trips.
- Index ranges on stacks — read a contiguous range of frames in one call.

## Display-time corrections

ptir5 returns stored samples. PTIR Studio applies several corrections only for
display, and optional helpers could reproduce them:

- Hyperspectral normalization math for the settings ptir5 already reports
  (`Peak`, `Wavenumber`, `Time`, `Offset`, including the NaN-gap reference
  fallback), per spec §13.4.
- PT-SRS power correction (divide by enabled `PumpPower` / `StokesPower`
  factors), per spec §6.4.
- Noise-frame add-back for images whose stored pixels had the noise frame
  subtracted at write.
- FL-PTIR per-frame background scale from the referenced background spectrum,
  per spec §9.6.

## Spectrum extraction from FL-PTIR stacks

- `read_spectrum(x, y)` and ROI bulk reads on FL-PTIR image stacks. Bulk reads
  must return pixel-major (interlaced) order for both storage formats; the C#
  SDK fixed exactly this bug for legacy rank-4 stacks (PS-3573).

## CLI tool

- `ptir5 inspect <file>` — print a structured summary of a `.ptir` file
  (measurements, types, shapes, dtypes, tree layout, key metadata).
- `--json` flag for machine-readable output suitable for piping into `jq` or
  another tool.

Useful for quick adoption, support debugging, and CI integration tests that
need to assert against file contents without writing Python glue.

## Ecosystem adapters

- Optional `xarray` export helper for hyperspectral workflows, so callers can
  drop a measurement straight into an `xarray.DataArray` with named axes and
  coordinates derived from `XStart` / `XIncrement` / pixel pitch.
- Optional `pandas` export for spectral-list workflows.

These should remain optional extras (`pip install ptir5[xarray]`) so the core
library doesn't grow heavyweight dependencies.
