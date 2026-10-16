#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

base_cleanup_paths=()
while IFS= read -r -d '' path; do
    base_cleanup_paths+=("$path")
done < <(
    find . \( -type d \( -name .git -o -name .venv -o -name venv -o -name env \) -prune \) -o \
        \( -type d \( -name __pycache__ -o -name .pytest_cache -o -name htmlcov -o -name build -o -name dist -o -name '*.egg-info' \) -prune -print0 \) -o \
        \( -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.pyd' -o -name '*.so' -o -name '.coverage' -o -name '.coverage.*' \) -print0 \)
)

extra_cleanup_paths=()
for path in .venv venv env uv.lock .python-version; do
    if [[ -e "$path" || -L "$path" ]]; then
        extra_cleanup_paths+=("./$path")
    fi
done
all_cleanup_paths=("${base_cleanup_paths[@]}" "${extra_cleanup_paths[@]}")

print_paths() {
    if [[ $# -eq 0 ]]; then
        printf '  (nothing)\n'
    else
        printf '  %s\n' "$@"
    fi
}

printf '1) Remove:\n'
print_paths "${base_cleanup_paths[@]}"
printf '2) Also remove these paths (plus everything in 1):\n'
print_paths "${extra_cleanup_paths[@]}"
printf 'q) Quit\n'
read -r -p 'Select [1/2/q]: ' choice

case "$choice" in
1) cleanup_paths=("${base_cleanup_paths[@]}") ;;
2) cleanup_paths=("${all_cleanup_paths[@]}") ;;
q | Q)
    printf 'Cleanup cancelled.\n'
    exit 0
    ;;
*)
    printf 'Invalid choice: %s\n' "$choice" >&2
    exit 2
    ;;
esac

if [[ ${#cleanup_paths[@]} -eq 0 ]]; then
    printf 'Nothing to remove.\n'
    exit 0
fi

rm -rf -- "${cleanup_paths[@]}"

printf 'Cleanup complete.\n'
