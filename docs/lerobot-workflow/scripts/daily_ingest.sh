#!/usr/bin/env bash
# 日终归档：staging → raw，更新 manifest
# 部署：cp 到 /data/scripts/daily_ingest.sh
# cron: 30 18 * * 1-6 root /data/scripts/daily_ingest.sh

set -euo pipefail

DATA_ROOT="${DATA_ROOT:-/data}"
SCRIPTS="${SCRIPTS:-$DATA_ROOT/scripts}"
DATE=$(date +%Y-%m-%d)
STAGING="$DATA_ROOT/staging/today"
RAW="$DATA_ROOT/raw/$DATE"
MANIFEST="$DATA_ROOT/raw/manifest.jsonl"
SCHEMA="$DATA_ROOT/raw/schema/v1_features.json"
LOG_DIR="$DATA_ROOT/builds/$DATE"

mkdir -p "$RAW" "$LOG_DIR"

if [[ ! -d "$STAGING" ]] || [[ -z "$(ls -A "$STAGING" 2>/dev/null)" ]]; then
  echo "[$DATE] staging empty, skip"
  exit 0
fi

for session_dir in "$STAGING"/*/; do
  [[ -d "$session_dir" ]] || continue
  session=$(basename "$session_dir")
  mkdir -p "$RAW/$session"

  for ep_dir in "$session_dir"/episode_*/; do
    [[ -d "$ep_dir" ]] || continue

    # ROS bag 导出（若存在 export_ros_episode.py）
    if [[ -f "$SCRIPTS/export_ros_episode.py" ]] && [[ -d "$ep_dir/ros" ]]; then
      python "$SCRIPTS/export_ros_episode.py" "$ep_dir" >> "$LOG_DIR/ingest.log" 2>&1
    fi

    python "$SCRIPTS/validate_episode.py" \
      --episode-dir "$ep_dir" \
      --schema "$SCHEMA" \
      --output "$ep_dir/validation.json" >> "$LOG_DIR/ingest.log" 2>&1 || true

    python "$SCRIPTS/append_manifest.py" \
      --episode-dir "$ep_dir" \
      --date "$DATE" \
      --session "$session" \
      --manifest "$MANIFEST" >> "$LOG_DIR/ingest.log" 2>&1

    mv "$ep_dir" "$RAW/$session/"
  done

  if [[ -f "$session_dir/session_meta.json" ]]; then
    cp "$session_dir/session_meta.json" "$RAW/$session/"
  fi
done

rm -rf "${STAGING:?}"/*
echo "[$DATE] ingest done → $RAW"

# 同步统计大看板（若已部署 robot-data-dashboard）
SYNC_SCRIPT="${DATA_ROOT}/dashboard/api/scripts/sync_stats_db.py"
if [[ -f "$SYNC_SCRIPT" ]]; then
  python3 "$SYNC_SCRIPT" --data-root "$DATA_ROOT" --event ingest --job-type daily_ingest || true
fi
