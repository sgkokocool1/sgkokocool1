#!/usr/bin/env bash
# 一键部署脚本到本地服务器 /data/scripts/
# 在 robot-server 上执行：bash deploy_to_server.sh /data

set -euo pipefail

TARGET="${1:-/data}"
REPO_SCRIPTS="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$TARGET/scripts" "$TARGET/raw/schema" "$TARGET/staging/today" "$TARGET/lerobot" "$TARGET/builds" "$TARGET/training"

cp -r "$REPO_SCRIPTS"/*.py "$REPO_SCRIPTS"/*.sh "$REPO_SCRIPTS/requirements.txt" "$TARGET/scripts/"
cp "$(dirname "$REPO_SCRIPTS")/examples/schema/v1_features.json" "$TARGET/raw/schema/"

chmod +x "$TARGET/scripts"/*.sh "$TARGET/scripts"/*.py

touch "$TARGET/raw/manifest.jsonl"

echo "deployed scripts → $TARGET/scripts"
echo "deployed schema  → $TARGET/raw/schema/v1_features.json"
echo ""
echo "next steps:"
echo "  pip install -r $TARGET/scripts/requirements.txt"
echo "  # 编辑 cron（见 README.md 第 8 节）"
