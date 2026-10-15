#!/usr/bin/env bash
# Build the deployable app bundle in build/mpy/.
#
# Every module in src/ is precompiled to .mpy with mpy-cross, except:
#   main.py    MicroPython only runs main.py from source at startup.
#   config.py  kept as source so settings stay readable and editable.
#   ble_scan.py  standalone diagnostic, not part of the app.
# Precompiled modules load faster and avoid compiling app.py on the board,
# which needs RAM and fragments the heap.
#
# Usage:
#   tools/build_mpy.sh              # writes build/mpy/
#   BUILD_DIR=/tmp/x tools/build_mpy.sh

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${BUILD_DIR:-$repo_root/build/mpy}"

python="python3"
if [[ -x "$repo_root/.venv/bin/python" ]]; then
    python="$repo_root/.venv/bin/python"
fi
if ! "$python" -m mpy_cross --version >/dev/null 2>&1; then
    echo "mpy-cross is missing; install the dev tools with:" >&2
    echo "  .venv/bin/python -m pip install -r requirements-dev.txt" >&2
    exit 1
fi

rm -rf "$build_dir"
mkdir -p "$build_dir"

for file in "$repo_root"/src/*.py; do
    name="$(basename "$file")"
    case "$name" in
        main.py | config.py)
            cp "$file" "$build_dir/$name"
            ;;
        ble_scan.py)
            ;;
        *)
            # -s sets the file name shown in tracebacks on the board.
            "$python" -m mpy_cross -s "$name" -o "$build_dir/${name%.py}.mpy" "$file"
            ;;
    esac
done

echo "Built $(ls "$build_dir" | wc -l) files in ${build_dir#"$repo_root"/} with $("$python" -m mpy_cross --version)"
