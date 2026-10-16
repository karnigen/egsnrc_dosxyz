# egsnrc_dosxyz

Read and write 3ddose and egsphant files.

## Setup

Run the setup script to pin Python 3.14 and synchronize the project environment:

```sh
./dev/010_setup_uv.sh
```

## Development

Install the project and its dependencies with [uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

Run Python commands in the project environment with `uv run`, and build the source
distribution and wheel with:

```sh
uv build
```

## Command-Line Tools

The executable tools use `uvr` in their shebangs, so make sure `uvr` is available on `PATH`.

Convert a dose and matching phantom from DICOM to DOSXYZ coordinates. The phantom base
defaults to the dose base, and `_1` is appended to both output names by default:

```sh
src/egsnrc_dosxyz/dcm2egs_3ddose.py dose_base [--phantom-base phantom_base] [--postfix _rotated] [--overwrite]
```

Convert a `.3ddose` file to a VTK rectilinear grid:

```sh
src/egsnrc_dosxyz/dose3d2vtr.py dose_base [--overwrite]
```

Convert gantry, couch, and collimator angles from DICOM to DOSXYZnrc angles (in degrees):

```sh
src/egsnrc_dosxyz/dcm2egs_angles.py 0 0 0
```

Join one or more IAEA headers and their matching `.IAEAphsp` binary files. The binary files
must be beside their headers and share the same base names:

```sh
src/egsnrc_dosxyz/iaeaphsp_header.py input1.IAEAheader input2.IAEAheader --output merged.IAEAheader
```

Add `--overwrite` to replace existing output files.

## Tests

Run the test suite with:

```sh
uv run pytest
```

## Examples

Read an IAEA phase-space header bundled with the examples:

```sh
uv run python examples/read_iaeaphsp_header.py
```

Read a 3ddose file and write it back to a new path:

```sh
uv run python examples/roundtrip_3ddose.py input.3ddose output.3ddose
```
