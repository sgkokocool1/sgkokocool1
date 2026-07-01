#!/usr/bin/env bash
# 按日期范围新建数据集（如：一个月数据只用第二周）
# 用法：DATE_FROM=2025-07-14 DATE_TO=2025-07-20 ./build_subset_dataset.sh

set -euo pipefail

DATA_ROOT="${DATA_ROOT:-/data}"
SCRIPTS="${SCRIPTS:-$DATA_ROOT/scripts}"

DATE_FROM="${DATE_FROM:?set DATE_FROM=YYYY-MM-DD}"
DATE_TO="${DATE_TO:?set DATE_TO=YYYY-MM-DD}"
DATASET_NAME="${DATASET_NAME:-pick-place-subset}"
BUILD_TAG="${BUILD_TAG:-${DATE_FROM}_to_${DATE_TO}}"

BUILD_DIR="$DATA_ROOT/builds/$BUILD_TAG"
MANIFEST="$DATA_ROOT/raw/manifest.jsonl"
SCHEMA="$DATA_ROOT/raw/schema/v1_features.json"
IMPORT_LIST="$BUILD_DIR/import_list.jsonl"
DATASET_ROOT="$DATA_ROOT/lerobot/${DATASET_NAME}"
REPO_ID="local/${DATASET_NAME}"

mkdir -p "$BUILD_DIR"

python3 "$SCRIPTS/filter_manifest.py" \
  --input "$MANIFEST" \
  --output "$IMPORT_LIST" \
  --date-from "$DATE_FROM" \
  --date-to "$DATE_TO" \
  --success-only

COUNT=$(wc -l < "$IMPORT_LIST" | tr -d ' ')
if [[ "$COUNT" == "0" ]]; then
  echo "no episodes in range $DATE_FROM .. $DATE_TO"
  exit 1
fi

python3 "$SCRIPTS/build_lerobot_dataset.py" \
  --mode create \
  --raw-root "$DATA_ROOT/raw" \
  --dataset-root "$DATASET_ROOT" \
  --repo-id "$REPO_ID" \
  --schema "$SCHEMA" \
  --import-list "$IMPORT_LIST" \
  --manifest "$MANIFEST" \
  --log-dir "$BUILD_DIR" \
  --streaming-encoding

echo "subset build done: $DATASET_ROOT ($COUNT episodes)"
