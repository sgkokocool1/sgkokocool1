#!/usr/bin/env bash
# 将 diagrams/*.mmd 渲染为 ../images/*.png
# 依赖：Node.js + npx @mermaid-js/mermaid-cli
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/../images"
mkdir -p "$OUT"

for f in "$DIR"/*.mmd; do
  name="$(basename "$f" .mmd)"
  echo "Rendering $name ..."
  npx -y @mermaid-js/mermaid-cli@11.4.0 \
    -i "$f" -o "$OUT/${name}.png" \
    -b white -w 1400 --scale 2
done

echo "Done. PNG → $OUT"
echo "Note: 09-ui-list-wireframe.png 为 UI 线框图，需单独维护（非 mermaid 渲染）"
