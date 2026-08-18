#!/usr/bin/env bash
set -euo pipefail
REPO=/home/ubuntu/voxelcreft-repo
ASSETS=/home/ubuntu/voxelcraft-version-downloads
MAP=$REPO/versions/downloads/RELEASE_MAP.tsv
cd "$REPO"
: > /tmp/voxelcraft-release-map.tsv
printf 'snapshot\ttag\tcommit\trelease_url\tasset_url\n' > /tmp/voxelcraft-release-map.tsv
while IFS=$'\t' read -r snapshot latest commit archive size sha; do
  [[ "$snapshot" == "snapshot" ]] && continue
  tag="voxelcraft-${snapshot//[^A-Za-z0-9._-]/-}"
  if ! git rev-parse "$tag" >/dev/null 2>&1; then
    git tag -a "$tag" "$commit" -m "VoxelCraft source snapshot $snapshot"
    git push origin "$tag" >/dev/null
  fi
  if ! gh release view "$tag" --repo Mateuspp115/voxelcraft-odyssey-HTML-Build >/dev/null 2>&1; then
    gh release create "$tag" --repo Mateuspp115/voxelcraft-odyssey-HTML-Build --target "$commit" --title "VoxelCraft ${snapshot} — código-fonte" --notes "Snapshot source-only do HTML ${snapshot}. A v14 é a referência mais recente. Nenhum APK é anexado." >/dev/null
  fi
  gh release upload "$tag" "$ASSETS/$archive" --repo Mateuspp115/voxelcraft-odyssey-HTML-Build --clobber >/dev/null
  url=$(gh release view "$tag" --repo Mateuspp115/voxelcraft-odyssey-HTML-Build --json url --jq .url)
  asset_url=$(gh release view "$tag" --repo Mateuspp115/voxelcraft-odyssey-HTML-Build --json assets --jq '.assets[] | select(.name=="'"$archive"'") | .browser_download_url')
  printf '%s\t%s\t%s\t%s\t%s\n' "$snapshot" "$tag" "$commit" "$url" "$asset_url" >> /tmp/voxelcraft-release-map.tsv
done < "$MAP"
cp /tmp/voxelcraft-release-map.tsv "$REPO/versions/downloads/RELEASE_MAP.tsv"
