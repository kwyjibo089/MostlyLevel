#!/usr/bin/env bash
# Capture the running dashboard as assets/<name>.png.
#
# Interrupts the app, calls save_screenshot() on the board, copies the BMP to
# a temporary folder, deletes it from the board, converts it to PNG with
# ImageMagick, and restarts the app.
#
# Usage:
#   tools/screenshot.sh                  # -> assets/screenshot.png
#   tools/screenshot.sh levelling        # -> assets/levelling.png
#   tools/screenshot.sh corners.bmp      # -> assets/corners.png
#   tools/screenshot.sh wedges.png       # -> assets/wedges.png
#   tools/screenshot.sh -p /dev/ttyACM0  # use a specific serial port
#   tools/screenshot.sh -n               # leave the app stopped afterwards

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mpremote="$repo_root/.venv/bin/mpremote"

port="auto"
after=(+ reset)

usage() {
    sed -n '2,15s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"
}

while getopts ":p:nh" option; do
    case "$option" in
        p) port="$OPTARG" ;;
        n) after=() ;;
        h) usage; exit 0 ;;
        :) echo "Option -$OPTARG needs a value." >&2; exit 2 ;;
        *) echo "Unknown option -$OPTARG." >&2; usage >&2; exit 2 ;;
    esac
done
shift $((OPTIND - 1))

if (($# > 1)); then
    echo "Give at most one file name." >&2
    exit 2
fi

name="${1:-screenshot.bmp}"
# The name is used on the board and inside a Python string: keep it simple.
if [[ ! "$name" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "Use a plain file name (letters, digits, '.', '_', '-'), not a path: $name" >&2
    exit 2
fi
# The PNG keeps the given name minus its extension: wedges.png -> wedges.png.
base="${name%.*}"
if [[ -z "$base" ]]; then
    echo "File name needs more than an extension: $name" >&2
    exit 2
fi
png="$repo_root/assets/$base.png"
# On the board: without an extension, or with any extension other than .bmp,
# append .bmp (wedges.png -> wedges.png.bmp).
if [[ "${name,,}" != *.bmp ]]; then
    name="$name.bmp"
fi

if [[ ! -x "$mpremote" ]]; then
    echo "mpremote not found at $mpremote; install it with:" >&2
    echo "  .venv/bin/python -m pip install mpremote" >&2
    exit 1
fi
if ! command -v magick >/dev/null; then
    echo "ImageMagick 'magick' is needed to convert the BMP to PNG." >&2
    exit 1
fi

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

# "resume" skips mpremote's automatic soft reset, which would clear the
# running app's state. Entering the raw REPL interrupts the app (like Ctrl+C),
# so save_screenshot() renders the last displayed screen.
"$mpremote" connect "$port" resume \
    + exec "save_screenshot('/$name')" \
    + fs cp ":$name" "$work_dir/$name" \
    + fs rm ":$name" \
    "${after[@]}"

if [[ ! -s "$work_dir/$name" ]]; then
    echo "No screenshot was copied from the board." >&2
    exit 1
fi

mkdir -p "$(dirname "$png")"
magick "$work_dir/$name" "$png"
echo "Saved ${png#"$repo_root"/}"
