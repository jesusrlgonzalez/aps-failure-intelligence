#!/usr/bin/env bash
# Builds the release evidence ZIP from a git ref. Used by .github/workflows/release.yml
# and by tests/test_release_bundle.py, so the published bundle and the tested one are the same.
# Usage: deploy/build_release_bundle.sh <ref> <out.zip> [assets list]
set -euo pipefail
ref=$1 out=$2 list=${3:-deploy/release-assets.txt}
keep=()
while IFS= read -r p || [ -n "$p" ]; do
  p=${p%%#*}; p=${p%"${p##*[![:space:]]}"}
  [ -z "$p" ] && continue
  git cat-file -e "$ref:$p" 2>/dev/null && keep+=("$p")   # older tags lack newer paths
done < "$list"
git cat-file -e "$ref:LICENSE" 2>/dev/null && keep+=("LICENSE")
git archive --format=zip -o "$out" "$ref" -- "${keep[@]}"
