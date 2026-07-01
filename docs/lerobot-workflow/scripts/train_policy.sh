#!/usr/bin/env bash
# 本地训练（指向已构建的 LeRobot 数据集）
# 用法：DATASET_NAME=pick-place-w2-202507 ./train_policy.sh

set -euo pipefail

DATA_ROOT="${DATA_ROOT:-/data}"
DATASET_NAME="${DATASET_NAME:-pick-place-v1}"
DATASET_ROOT="$DATA_ROOT/lerobot/$DATASET_NAME"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d-%H%M)}"
OUTPUT_DIR="$DATA_ROOT/training/${DATASET_NAME}-${RUN_TAG}"

if [[ ! -f "$DATASET_ROOT/meta/info.json" ]]; then
  echo "dataset not found: $DATASET_ROOT"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

lerobot-train \
  --dataset.repo_id="local/$DATASET_NAME" \
  --dataset.root="$DATASET_ROOT" \
  --policy.type=act \
  --output_dir="$OUTPUT_DIR" \
  --training.num_epochs=100 \
  --training.batch_size=32 \
  2>&1 | tee "$OUTPUT_DIR/train.log"

echo "training done → $OUTPUT_DIR"
