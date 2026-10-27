#!/usr/bin/env bash
# Publish the Hugging Face dataset prteek/user-journey-dau (locally: `hf auth login` as prteek; in CI: HF_TOKEN):
#   records  dau_data.csv with dataset/README.md as the card (what CI publishes)
#   space    prteek/user-journey-what-if: space/ (app, card, requirements, baseline.json) plus user_journey/model.py
# The user states are not published: `python -m user_journey.states` builds them from dau_data.csv in seconds.
# Usage: ./publish.sh [message] [records|space ...]   (default: records)
# Set HF_CLI=hf to use an installed hf CLI instead of `uvx hf`.
set -euo pipefail
cd "$(dirname "$0")"
msg="${1:-Update}"
shift || true
if [ $# -gt 0 ]; then targets=("$@"); else targets=(records); fi
read -r -a hf <<< "${HF_CLI:-uvx --from huggingface_hub hf}"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

for t in "${targets[@]}"; do
  case "$t" in
    records)
      mkdir "$stage/records"
      cp dau_data.csv "$stage/records/"
      cp dataset/README.md "$stage/records/README.md"
      "${hf[@]}" upload prteek/user-journey-dau "$stage/records" . --repo-type dataset --commit-message "$msg" ;;
    space)
      mkdir -p "$stage/space/user_journey"
      cp space/app.py space/README.md space/requirements.txt space/baseline.json "$stage/space/"
      cp user_journey/__init__.py user_journey/model.py "$stage/space/user_journey/"
      "${hf[@]}" upload prteek/user-journey-what-if "$stage/space" . --repo-type space --commit-message "$msg" ;;
    *)
      echo "unknown target: $t" >&2; exit 1 ;;
  esac
done
