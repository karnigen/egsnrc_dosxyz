# egsnrc_dosxyz

Read and write 3ddose and egsphant files.

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
