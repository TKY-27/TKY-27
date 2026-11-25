#!/bin/sh
# Regenerate every image in assets/.
# Needs uv and gh, the Spikes, Metrica and CelestialModern fonts under ~/Fonts,
# ~/Desktop/icon.png, and the MacEase, OpenShogiUI and qrnel checkouts under ~/Projects.
set -eu
cd "$(dirname "$0")/.."
run="uv run -q --python 3.12 --with fonttools --with uharfbuzz --with pillow --with segno python"
$run tools/build_hero.py assets
$run tools/build_icons.py assets/icons
$run tools/build_wordmarks.py assets/type
$run tools/build_qr.py assets/icons/scan.svg
python3 tools/build_habits.py assets
python3 tools/stamp_readme.py README.md assets/hero-light.svg
