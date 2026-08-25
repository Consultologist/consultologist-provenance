#!/usr/bin/env bash
# Publish the provenance registry — the record contract, the hash definitions
# and the registry layout — to the PUBLIC registry and update its
# latest-pointer. The document set is a versioned artifact
# (provenance-versions.json declares its own CalVer version); published
# versions are immutable — this script refuses to overwrite an existing
# version. The engine does not fetch this at runtime: it vendors this repo as
# a submodule, and a test there asserts its hash constants and record storage
# versions match the index and that the worked examples recompute, so the
# two cannot silently disagree.
#
# Usage:
#   ./scripts/publish-provenance.sh <storage-account>
# Example:
#   ./scripts/publish-provenance.sh consultologistpublic
set -euo pipefail

CONTAINER="provenance"
INDEX="provenance-versions.json"

if [[ $# -ne 1 ]]; then
	# 1d drops the shebang, which grep '^#' would otherwise print as usage.
	grep '^#' "$0" | sed -e '1d' -e 's/^# \{0,1\}//' | head -13
	exit 1
fi

ACCOUNT="$1"

[[ -f "$INDEX" ]] || { echo "error: $INDEX not found (run from the repo root)" >&2; exit 1; }

VERSION=$(python3 -c "import json;print(json.load(open('$INDEX'))['version'])")

if ! [[ "$VERSION" =~ ^v[0-9]{4}\.[0-9]{2}\.[1-9][0-9]*$ ]]; then
	echo "error: version '$VERSION' is not vYYYY.MM.N" >&2
	exit 1
fi

AUTH=(--account-name "$ACCOUNT" --auth-mode "${AZ_STORAGE_AUTH_MODE:-login}")

if az storage blob exists "${AUTH[@]}" --container-name "$CONTAINER" \
	--name "$VERSION/$INDEX" --query exists -o tsv | grep -q true; then
	echo "error: provenance@$VERSION is already published; versions are immutable — bump the version" >&2
	exit 1
fi

# Documents first, the index last (a reader resolves the index first, so a
# partial upload is invisible) — the ordering publish-output-contracts.sh uses.
python3 -c "
import json
for f in json.load(open('$INDEX'))['documents'].values(): print(f)
" | sort -u | while read -r DOC; do
	[[ -f "$DOC" ]] || { echo "error: document $DOC named by $INDEX not found" >&2; exit 1; }
	echo "Uploading $VERSION/$DOC"
	az storage blob upload "${AUTH[@]}" --container-name "$CONTAINER" \
		--file "$DOC" --name "$VERSION/$DOC" --output none
done

# The licence travels with the artifact. Somebody who downloads a version out
# of the registry to re-verify a consult should not have to come back to GitHub
# to learn what they may do with it.
echo "Uploading $VERSION/LICENSE"
az storage blob upload "${AUTH[@]}" --container-name "$CONTAINER" \
	--file LICENSE --name "$VERSION/LICENSE" --output none

echo "Uploading $VERSION/$INDEX"
az storage blob upload "${AUTH[@]}" --container-name "$CONTAINER" \
	--file "$INDEX" --name "$VERSION/$INDEX" --output none

echo "Updating latest.json -> $VERSION"
POINTER=$(mktemp)
printf '{"version": "%s"}\n' "$VERSION" > "$POINTER"
az storage blob upload "${AUTH[@]}" --container-name "$CONTAINER" \
	--file "$POINTER" --name "latest.json" --overwrite --output none
rm -f "$POINTER"

echo "Published provenance@$VERSION and updated latest pointer."
