#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v uv >/dev/null 2>&1; then
    printf 'uv is required. Install it from https://docs.astral.sh/uv/\n' >&2
    exit 1
fi

printf 'This setup will:\n'
printf '  - pin the project Python version to 3.14 in .python-version\n'
printf '  - create or update uv.lock\n'
printf '  - synchronize the project environment with uv sync --python 3.14\n'

if [[ -e .venv || -L .venv ]]; then
    printf '\nAn existing .venv was found. It will be deleted and recreated.\n'
    read -r -p 'Continue and replace .venv? [y/N] ' confirm
    default_answer=n
else
    printf '\nNo existing .venv was found; setup will create one.\n'
    read -r -p 'Continue? [Y/n] ' confirm
    default_answer=y
fi

if [[ -z "$confirm" ]]; then
    confirm="$default_answer"
fi

case "$confirm" in
y | Y) ;;
*)
    printf 'Setup cancelled.\n'
    exit 0
    ;;
esac

if [[ -e .venv || -L .venv ]]; then
    rm -rf -- .venv
fi

uv python pin 3.14
uv sync --python 3.14
