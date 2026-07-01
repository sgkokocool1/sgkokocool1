#!/usr/bin/env bash
# 每周日：校验 manifest 与 raw 目录一致性
# cron: 0 10 * * 0 root /data/scripts/weekly_qc.sh

set -euo pipefail

DATA_ROOT="${DATA_ROOT:-/data}"
SCRIPTS="${SCRIPTS:-$DATA_ROOT/scripts}"

python3 "$SCRIPTS/weekly_qc.py" --raw-root "$DATA_ROOT/raw"
echo "weekly QC passed"
