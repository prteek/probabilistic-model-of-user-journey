#!/usr/bin/env bash
# Publish the Hugging Face dataset prteek/user-journey-dau: dau_data.csv with huggingface/dataset/README.md as the
# card (locally: `hf auth login` as prteek; in CI: HF_TOKEN).
# Usage: huggingface/publish.sh [message]
# Set HF_CLI=hf to use an installed hf CLI instead of `uvx hf`.
set -euo pipefail
cd "$(dirname "$0")/.."
msg="${1:-Update}"
read -r -a hf <<< "${HF_CLI:-uvx --from huggingface_hub hf}"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

cp dau_data.csv "$stage/"
cp huggingface/dataset/README.md "$stage/README.md"
"${hf[@]}" upload prteek/user-journey-dau "$stage" . --repo-type dataset --commit-message "$msg"
