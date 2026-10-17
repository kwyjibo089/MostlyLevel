#!/usr/bin/env bash
# Refresh the README screen images in the root assets/ from the reference images in
# tests/golden/, which the desktop tests render with the app's own drawing
# code (a device screenshot of the VAN view matched them on 2026-10-16).
# Images are scaled 2x without smoothing so the pixels stay crisp.
#
# Usage: tools/readme_images.sh   (needs ImageMagick's `magick`)

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
golden="$repo_root/tests/golden"
assets="$repo_root/../assets"
mkdir -p "$assets"

for name in van_live van_level horizon_live horizon_tilted levelling_wedges levelling_corners de_van_live fr_horizon_stale; do
    magick "$golden/$name.png" -filter point -resize 200% "$assets/readme-${name//_/-}.png"
done
echo "Updated README images in $assets/"
