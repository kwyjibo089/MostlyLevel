#!/usr/bin/env bash
# Run all checks that CI runs: ruff, the MicroPython compiler, and pytest.
#
# Usage:
#   tools/test.sh                   # everything
#   tools/test.sh -k levelling      # extra arguments go to pytest
#   tools/test.sh --update-golden   # rewrite tests/golden/*.png, then review them

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# Use the project venv locally; CI installs the tools into its own Python.
python="python3"
if [[ -x .venv/bin/python ]]; then
    python=".venv/bin/python"
fi

echo "== ruff"
"$python" -m ruff check .

echo "== mpy-cross (MicroPython syntax check)"
out_dir="$(mktemp -d)"
trap 'rm -rf "$out_dir"' EXIT
for file in src/*.py; do
    "$python" -m mpy_cross -o "$out_dir/$(basename "${file%.py}").mpy" "$file"
done
echo "compiled $(ls "$out_dir" | wc -l) files"

echo "== pytest"
"$python" -m pytest "$@"
