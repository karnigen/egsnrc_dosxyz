#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v uv >/dev/null 2>&1; then
    printf 'uv is required. Install it from https://docs.astral.sh/uv/\n' >&2
    exit 1
fi

run_all_checks() {
    uv run pytest
    uv run ruff check .
    uv build
}

printf 'Choose checks to run:\n'
printf '  1) Tests (choose all tests or a test module)\n'
printf '  2) Ruff lint\n'
printf '  3) Build package\n'
printf '  4) All checks (tests, Ruff lint, build)\n'
printf '  q) Quit\n'
read -r -p 'Select [1-4/q]: ' choice

case "$choice" in
1) exec ./dev/040_tests.sh ;;
2) exec uv run ruff check . ;;
3) exec uv build ;;
4) run_all_checks ;;
q | Q)
    printf 'Checks cancelled.\n'
    exit 0
    ;;
*)
    printf 'Invalid choice: %s\n' "$choice" >&2
    exit 2
    ;;
esac
