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
