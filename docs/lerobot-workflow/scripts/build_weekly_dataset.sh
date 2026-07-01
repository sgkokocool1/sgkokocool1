#!/usr/bin/env bash
# 每周五：增量构建 LeRobot 数据集（resume 模式）
# cron: 45 18 * * 5 root /data/scripts/build_weekly_dataset.sh

set -euo pipefail

DATA_ROOT="${DATA_ROOT:-/data}"
SCRIPTS="${SCRIPTS:-$DATA_ROOT/scripts}"
WEEK_TAG=$(date +%Y-W%V)
BUILD_DIR="$DATA_ROOT/builds/$WEEK_TAG"
MANIFEST="$DATA_ROOT/raw/manifest.jsonl"
SCHEMA="$DATA_ROOT/raw/schema/v1_features.json"
DATASET_ROOT="$DATA_ROOT/lerobot/pick-place-v1"
REPO_ID="local/pick-place-v1"
IMPORT_LIST="$BUILD_DIR/import_list_pending.jsonl"

mkdir -p "$BUILD_DIR"

# 筛选：尚未导入的成功 episode（全量 pending）
python3 - <<'PY' "$MANIFEST" "$IMPORT_LIST"
import json, sys
manifest, out = sys.argv[1], sys.argv[2]
pending = []
with open(manifest) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("success") and rec.get("imported_to") is None:
            pending.append(rec)
with open(out, "w") as f:
    for rec in pending:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"pending {len(pending)} → {out}")
PY

COUNT=$(wc -l < "$IMPORT_LIST" | tr -d ' ')
if [[ "$COUNT" == "0" ]]; then
  echo "no pending episodes, skip build"
  exit 0
fi

MODE="create"
if [[ -f "$DATASET_ROOT/meta/info.json" ]]; then
  MODE="resume"
fi

python3 "$SCRIPTS/build_lerobot_dataset.py" \
  --mode "$MODE" \
  --raw-root "$DATA_ROOT/raw" \
  --dataset-root "$DATASET_ROOT" \
  --repo-id "$REPO_ID" \
  --schema "$SCHEMA" \
  --import-list "$IMPORT_LIST" \
  --manifest "$MANIFEST" \
  --log-dir "$BUILD_DIR" \
  --streaming-encoding

echo "weekly build done: mode=$MODE episodes_imported=$COUNT"
