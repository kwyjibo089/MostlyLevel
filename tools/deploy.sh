#!/usr/bin/env bash
# Upload the MostlyLevel app to the ESP32 in one mpremote session, then reset.
#
# mpremote (1.23+) compares each file's SHA-256 with the copy on the board and
# skips unchanged files ("Up to date"), so uploading everything is cheap.
#
# Usage:
#   tools/deploy.sh                    # all app files in src/ except ble_scan.py
#   tools/deploy.sh src/main.py ...    # only the given files
#   tools/deploy.sh -p /dev/ttyACM0    # use a specific serial port
#   tools/deploy.sh -f                 # copy even if unchanged
#   tools/deploy.sh -n                 # do not reset the board afterwards
#   tools/deploy.sh -r                 # open the REPL after uploading (no reset)

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mpremote="$repo_root/.venv/bin/mpremote"

port="auto"
force=()
after=(+ reset)

usage() {
    sed -n '2,13s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"
}

while getopts ":p:fnrh" option; do
    case "$option" in
        p) port="$OPTARG" ;;
        f) force=(--force) ;;
        n) after=() ;;
        r) after=(+ repl) ;;
        h) usage; exit 0 ;;
        :) echo "Option -$OPTARG needs a value." >&2; exit 2 ;;
        *) echo "Unknown option -$OPTARG." >&2; usage >&2; exit 2 ;;
    esac
done
shift $((OPTIND - 1))

if [[ ! -x "$mpremote" ]]; then
    echo "mpremote not found at $mpremote; install it with:" >&2
    echo "  .venv/bin/python -m pip install mpremote" >&2
    exit 1
fi

files=()
if (($#)); then
    files=("$@")
else
    for file in "$repo_root"/src/*.py; do
        # Standalone BLE discovery diagnostic; the dashboard does not import it.
        [[ "$(basename "$file")" == "ble_scan.py" ]] && continue
        files+=("$file")
    done
fi

for file in "${files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "No such file: $file" >&2
        exit 1
    fi
done

# Files go to the board's filesystem root because main.py imports by name.
"$mpremote" connect "$port" fs cp "${force[@]}" "${files[@]}" : "${after[@]}"
