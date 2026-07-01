#!/usr/bin/env python3
"""读取 episode_meta.json，追加一行到 manifest.jsonl。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append one episode record to manifest.jsonl")
    parser.add_argument("--episode-dir", type=Path, required=True)
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--session", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--schema", default="v1")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    meta_path = args.episode_dir / "episode_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing {meta_path}")

    meta = json.loads(meta_path.read_text())
    episode_name = args.episode_dir.name

    record = {
        "date": args.date,
        "session": args.session,
        "episode": episode_name,
        "source": meta.get("source", "ros"),
        "task": meta.get("task", ""),
        "success": bool(meta.get("success", False)),
        "fps": meta.get("fps", 30),
        "frames": meta.get("frames", 0),
        "schema": args.schema,
        "path": f"{args.date}/{args.session}/{episode_name}",
        "imported_to": None,
        "imported_at": None,
    }

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"appended {record['path']} → {args.manifest}")


if __name__ == "__main__":
    main()
