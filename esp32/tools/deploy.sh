#!/usr/bin/env bash
# Build and upload the MostlyLevel app to the ESP32 in one mpremote session.
#
# By default this builds build/mpy/ (precompiled .mpy modules plus main.py
# and config.py as source, see tools/build_mpy.sh), checks that the board
# accepts the .mpy format, uploads the bundle, removes stale .py copies of
# precompiled modules (MicroPython would load foo.py before foo.mpy), and
# resets the board. mpremote skips files that are unchanged on the board.
#
# Usage:
#   tools/deploy.sh                    # build .mpy bundle, upload, reset
#   tools/deploy.sh -s                 # upload .py sources instead of .mpy
#   tools/deploy.sh src/ble_scan.py    # upload only the given files, as-is
#   tools/deploy.sh -p /dev/ttyACM0    # use a specific serial port
#   tools/deploy.sh -f                 # copy even if unchanged
#   tools/deploy.sh -n                 # do not reset the board afterwards
#   tools/deploy.sh -r                 # open the REPL after uploading (no reset)

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mpremote="${MPREMOTE:-$repo_root/.venv/bin/mpremote}"
build_dir="${BUILD_DIR:-$repo_root/build/mpy}"

port="auto"
force=()
after=(+ reset)
mode="mpy"

usage() {
    sed -n '2,19s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"
}

while getopts ":p:fnrsh" option; do
    case "$option" in
        p) port="$OPTARG" ;;
        f) force=(--force) ;;
        n) after=() ;;
        r) after=(+ repl) ;;
        s) mode="source" ;;
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

# Python run on the board after copying: delete the given files if present.
remove_on_board() {
    local names=""
    local name
    for name in "$@"; do
        names+="'$name',"
    done
    printf 'import os\nfor name in (%s):\n    try:\n        os.remove(name)\n        print("Removed stale", name)\n    except OSError:\n        pass\n' "$names"
}

files=()
before=()
cleanup=()

if (($#)); then
    # Explicit files: upload exactly these, nothing else.
    for file in "$@"; do
        if [[ ! -f "$file" ]]; then
            echo "No such file: $file" >&2
            exit 1
        fi
        files+=("$file")
    done
elif [[ "$mode" == "source" ]]; then
    stale=()
    for file in "$repo_root"/src/*.py; do
        name="$(basename "$file")"
        # Standalone BLE discovery diagnostic; the dashboard does not import it.
        [[ "$name" == "ble_scan.py" ]] && continue
        files+=("$file")
        [[ "$name" != "main.py" ]] && stale+=("${name%.py}.mpy")
    done
    files+=("$repo_root"/../shared/i18n/lang_*.json)
    cleanup=(+ exec "$(remove_on_board "${stale[@]}")")
else
    BUILD_DIR="$build_dir" "$repo_root/tools/build_mpy.sh"
    stale=()
    for file in "$build_dir"/*; do
        files+=("$file")
        name="$(basename "$file")"
        [[ "$name" == *.mpy ]] && stale+=("${name%.mpy}.py")
    done

    # The board must accept the built .mpy major version. Bytecode-only
    # files leave the arch/sub-version header byte at 0, so only native code
    # would also need a matching sub-version; mpy-cross is not asked for it.
    read -r _ built_version built_flags < <(od -An -tu1 -N3 "$build_dir/app.mpy")
    if ((built_flags != 0)); then
        echo "Unexpected native code in the .mpy build (flags $built_flags)." >&2
        exit 1
    fi
    before=(exec "import sys
v = getattr(sys.implementation, '_mpy', None)
if v is not None and (v & 0xFF) != $built_version:
    raise RuntimeError('board loads .mpy version %d but the build is $built_version; use a matching mpy-cross or deploy -s' % (v & 0xFF))" +)
    cleanup=(+ exec "$(remove_on_board "${stale[@]}")")
fi

# Files go to the board's filesystem root because main.py imports by name.
"$mpremote" connect "$port" "${before[@]}" fs cp "${force[@]}" "${files[@]}" : \
    "${cleanup[@]}" "${after[@]}"
