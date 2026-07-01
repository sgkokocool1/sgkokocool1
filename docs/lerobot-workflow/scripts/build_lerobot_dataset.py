#!/usr/bin/env python3
"""
从 raw 层 import_list 构建 LeRobot v3 数据集。

支持两种模式：
  create — 新建数据集（如：只用第二周数据）
  resume — 向已有数据集追加 episode（如：每周五增量）
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# 同目录模块
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from load_episode import load_episode  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build LeRobot v3 dataset from raw import_list")
    parser.add_argument("--mode", choices=["create", "resume"], required=True)
    parser.add_argument("--raw-root", type=Path, required=True, help="/data/raw")
    parser.add_argument("--dataset-root", type=Path, required=True, help="/data/lerobot/xxx")
    parser.add_argument("--repo-id", required=True, help='如 "local/pick-place-w2-202507"')
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--import-list", type=Path, required=True, help="import_list.jsonl")
    parser.add_argument("--manifest", type=Path, default=None, help="默认 raw-root/manifest.jsonl")
    parser.add_argument("--log-dir", type=Path, default=None)
    parser.add_argument("--streaming-encoding", action="store_true")
    return parser.parse_args()


def load_import_list(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_report(
    args: argparse.Namespace,
    pending: list[dict],
    imported_paths: list[str],
    total_frames: int,
) -> dict:
    by_source: dict[str, int] = {}
    by_task: dict[str, int] = {}
    for rec in pending:
        if rec["path"] in imported_paths:
            by_source[rec["source"]] = by_source.get(rec["source"], 0) + 1
            by_task[rec["task"]] = by_task.get(rec["task"], 0) + 1

    return {
        "build_time": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "dataset_id": args.repo_id,
        "dataset_root": str(args.dataset_root),
        "import_list": str(args.import_list),
        "imported_episodes": len(imported_paths),
        "total_frames": total_frames,
        "by_source": by_source,
        "by_task": by_task,
    }


def main() -> None:
    args = parse_args()
    manifest = args.manifest or (args.raw_root / "manifest.jsonl")
    schema = json.loads(args.schema.read_text())
    pending = load_import_list(args.import_list)

    if not pending:
        print("import_list is empty, nothing to do")
        return

    try:
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
    except ImportError as e:
        raise ImportError(
            "需要安装 lerobot：pip install lerobot 或从 GitHub main 分支安装 v3 支持版本"
        ) from e

    if args.mode == "create":
        if args.dataset_root.exists() and (args.dataset_root / "meta/info.json").exists():
            raise FileExistsError(
                f"Dataset already exists at {args.dataset_root}. Use --mode resume or pick a new path."
            )
        dataset = LeRobotDataset.create(
            repo_id=args.repo_id,
            root=args.dataset_root,
            fps=schema["fps"],
            robot_type=schema.get("robot_type", "custom_arm"),
            features=schema["features"],
            use_videos=True,
            streaming_encoding=args.streaming_encoding,
        )
    else:
        if not (args.dataset_root / "meta/info.json").exists():
            raise FileNotFoundError(f"No existing dataset at {args.dataset_root}. Use --mode create first.")
        dataset = LeRobotDataset.resume(
            repo_id=args.repo_id,
            root=args.dataset_root,
            streaming_encoding=args.streaming_encoding,
        )

    imported_paths: list[str] = []
    total_frames = 0
    feature_keys = list(schema["features"].keys())

    for i, rec in enumerate(pending):
        ep_dir = args.raw_root / rec["path"]
        if not ep_dir.exists():
            raise FileNotFoundError(f"[{i}] missing episode dir: {ep_dir}")

        states, actions, images = load_episode(ep_dir, source=rec["source"])
        n = len(states)
        total_frames += n

        for t in range(n):
            frame: dict = {
                "observation.state": states[t],
                "action": actions[t],
                "task": rec["task"],
            }
            for cam_key, img_list in images.items():
                feature_name = f"observation.images.{cam_key}"
                if feature_name in feature_keys:
                    frame[feature_name] = img_list[t]
            dataset.add_frame(frame)

        dataset.save_episode()
        imported_paths.append(rec["path"])
        print(f"[{i + 1}/{len(pending)}] saved {rec['path']} ({n} frames)")

    dataset.finalize()
    print(f"finalized → {args.dataset_root}")

    # 更新 manifest
    from update_manifest_imported import load_paths  # noqa: E402

    imported_set = load_paths(args.import_list)
    now = datetime.now(timezone.utc).isoformat()
    if manifest.exists():
        records: list[dict] = []
        with manifest.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row.get("path") in imported_set:
                    row["imported_to"] = args.repo_id
                    row["imported_at"] = now
                records.append(row)
        with manifest.open("w") as f:
            for row in records:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"manifest updated → {manifest}")

    report = build_report(args, pending, imported_paths, total_frames)
    if args.log_dir:
        args.log_dir.mkdir(parents=True, exist_ok=True)
        report_path = args.log_dir / "import_report.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(f"report → {report_path}")

    info = json.loads((args.dataset_root / "meta/info.json").read_text())
    print(
        f"done: episodes={info['total_episodes']} frames={info['total_frames']} tasks={info['total_tasks']}"
    )


if __name__ == "__main__":
    main()
