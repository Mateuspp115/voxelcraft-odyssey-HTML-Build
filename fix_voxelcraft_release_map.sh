#!/usr/bin/env bash
set -euo pipefail
REPO=/home/ubuntu/voxelcreft-repo
IN=$REPO/versions/downloads/RELEASE_MAP.tsv
OUT=/tmp/voxelcraft-release-map-fixed.tsv
head -n 1 "$IN" > "$OUT"
tail -n +2 "$IN" | while IFS=$'\t' read -r snapshot tag commit release_url asset_url; do
  archive=$(grep -F "voxelcraft-${snapshot}-source.zip" -m1 /dev/null 2>/dev/null || true)
  # Derive the exact asset name from the version snapshot.
  name="voxelcraft-${snapshot}-source.zip"
  url=$(gh api "repos/Mateuspp115/voxelcraft-odyssey-HTML-Build/releases/tags/${tag}" --jq ".assets[] | select(.name==\"${name}\") | .browser_download_url")
  test -n "$url"
  printf '%s\t%s\t%s\t%s\t%s\n' "$snapshot" "$tag" "$commit" "$release_url" "$url" >> "$OUT"
done
mv "$OUT" "$IN"
