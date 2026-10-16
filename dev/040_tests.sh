#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v uv >/dev/null 2>&1; then
    printf 'uv is required. Install it from https://docs.astral.sh/uv/\n' >&2
    exit 1
fi

if [[ $# -gt 0 ]]; then
    exec uv run pytest "$@"
fi

printf 'Choose tests to run:\n'
printf '  1) All tests\n'
printf '  2) DICOM dose conversion\n'
printf '  3) DICOM angle conversion\n'
printf '  4) VTK dose export\n'
printf '  5) .3ddose file I/O\n'
printf '  6) egsphant file I/O\n'
printf '  7) IAEA phase-space headers\n'
printf '  q) Quit\n'
read -r -p 'Select [1-7/q]: ' choice

case "$choice" in
1) exec uv run pytest ;;
2) exec uv run pytest tests/test_dcm2egs_3ddose.py ;;
3) exec uv run pytest tests/test_dcm2egs_angles.py ;;
4) exec uv run pytest tests/test_dose3d2vtr.py ;;
5) exec uv run pytest tests/test_egs3ddose.py ;;
6) exec uv run pytest tests/test_egsphant.py ;;
7) exec uv run pytest tests/test_iaeaphsp_header.py ;;
q | Q)
    printf 'Tests cancelled.\n'
    exit 0
    ;;
*)
    printf 'Invalid choice: %s\n' "$choice" >&2
    exit 2
    ;;
esac
