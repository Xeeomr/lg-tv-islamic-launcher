#!/usr/bin/env bash
# Adds the Thmanyah typeface to the launcher from the zip you downloaded yourself
# (https://thmanyah.com/font — free download, its licence does not allow redistribution,
# so it is not part of this repository). Without it the UI uses Noto Sans Arabic.
# Usage: scripts/add-thmanyah.sh ~/Downloads/Thmanyah-Font-Family.zip
set -euo pipefail
cd "$(dirname "$0")/.."
zip="${1:?Pass the path of Thmanyah-Font-Family.zip}"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
unzip -q "$zip" -d "$tmp"
copy() { found="$(find "$tmp" -type f -name "$1" | head -n 1)"; [[ -n "$found" ]] || { echo "Missing $1 in the zip" >&2; exit 1; }; cp "$found" "launcher/fonts/$1"; }
for w in Light Regular Medium Bold; do copy "thmanyahsans-$w.woff2"; done
for w in Regular Medium; do copy "thmanyahseriftext-$w.woff2"; done
echo "Thmanyah added. Run ./install.sh <TV-IP> again to put it on the TV."
