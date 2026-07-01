#!/usr/bin/env python3
"""校验单个 episode 目录：文件存在性、帧数一致性。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one raw episode directory")
    parser.add_argument("--episode-dir", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None, help="写入 validation.json")
    return parser.parse_args()


def count_images(frames_dir: Path) -> int:
    if not frames_dir.exists():
        return 0
    return len(list(frames_dir.glob("*.jpg"))) + len(list(frames_dir.glob("*.png")))


def validate_ros_episode(ep_dir: Path, expected_frames: int) -> list[str]:
    errors: list[str] = []
    export = ep_dir / "export"
    for name in ("states.parquet", "actions.parquet"):
        if not (export / name).exists():
            errors.append(f"missing export/{name}")

    front = count_images(ep_dir / "cameras/front/frames")
    wrist = count_images(ep_dir / "cameras/wrist/frames")
    if expected_frames > 0:
        if front and front != expected_frames:
            errors.append(f"front frames={front}, expected={expected_frames}")
        if wrist and wrist != expected_frames:
            errors.append(f"wrist frames={wrist}, expected={expected_frames}")
    return errors


def validate_sim_episode(ep_dir: Path) -> list[str]:
    errors: list[str] = []
    if not (ep_dir / "rollout.hdf5").exists() and not (ep_dir / "rgb_front.mp4").exists():
        errors.append("missing rollout.hdf5 or rgb_front.mp4")
    return errors


def main() -> None:
    args = parse_args()
    meta_path = args.episode_dir / "episode_meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing {meta_path}")

    meta = json.loads(meta_path.read_text())
    source = meta.get("source", "ros")
    expected_frames = int(meta.get("frames", 0))

    errors: list[str] = []
    if source == "ros":
        errors.extend(validate_ros_episode(args.episode_dir, expected_frames))
    elif source == "sim":
        errors.extend(validate_sim_episode(args.episode_dir))
    elif source == "mp4":
        if not list(args.episode_dir.glob("**/*.mp4")):
            errors.append("missing mp4 file")
    else:
        errors.append(f"unknown source: {source}")

    result = {
        "episode_dir": str(args.episode_dir),
        "source": source,
        "valid": len(errors) == 0,
        "errors": errors,
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")

    if errors:
        print(f"INVALID {args.episode_dir}: {errors}")
        raise SystemExit(1)
    print(f"OK {args.episode_dir}")


if __name__ == "__main__":
    main()
