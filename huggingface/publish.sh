#!/usr/bin/env bash
# Publish the Hugging Face dataset prteek/user-journey-dau (locally: `hf auth login` as prteek; in CI: HF_TOKEN):
#   records  dau_data.csv with huggingface/dataset/README.md as the card (what CI publishes)
#   states   states.parquet: states.csv from prepare_states.r, converted to Parquet (needs the duckdb CLI);
#            published by hand because states.csv (~2.5 GB) is not in git
# Usage: huggingface/publish.sh [message] [records|states ...]   (default: records)
# Set HF_CLI=hf to use an installed hf CLI instead of `uvx hf`.
set -euo pipefail
cd "$(dirname "$0")/.."
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
      cp huggingface/dataset/README.md "$stage/records/README.md"
      "${hf[@]}" upload prteek/user-journey-dau "$stage/records" . --repo-type dataset --commit-message "$msg" ;;
    states)
      if [ ! -f states.parquet ] || [ states.csv -nt states.parquet ]; then
        duckdb -init /dev/null -c "COPY (FROM read_csv_auto('states.csv')) TO 'states.parquet' (FORMAT parquet, COMPRESSION zstd)"
      fi
      "${hf[@]}" upload prteek/user-journey-dau states.parquet states.parquet --repo-type dataset --commit-message "$msg" ;;
    *)
      echo "unknown target: $t" >&2; exit 1 ;;
  esac
done
