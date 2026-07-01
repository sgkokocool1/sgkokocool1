#!/usr/bin/env python3
"""从 raw episode 目录加载 states、actions、images。按 source 分发。"""

from __future__ import annotations

from pathlib import Path

import numpy as np


def read_jpg(path: Path) -> np.ndarray:
    try:
        from PIL import Image
    except ImportError as e:
        raise ImportError("load_episode 需要 pillow：pip install pillow") from e
    return np.array(Image.open(path).convert("RGB"))


def load_images_from_dir(frames_dir: Path, num_frames: int) -> list[np.ndarray]:
    if not frames_dir.exists():
        raise FileNotFoundError(f"Missing frames dir: {frames_dir}")
    images: list[np.ndarray] = []
    for i in range(num_frames):
        jpg = frames_dir / f"{i:06d}.jpg"
        png = frames_dir / f"{i:06d}.png"
        if jpg.exists():
            images.append(read_jpg(jpg))
        elif png.exists():
            images.append(read_jpg(png))
        else:
            raise FileNotFoundError(f"Missing frame: {jpg}")
    return images


def load_ros_episode(ep_dir: Path) -> tuple[np.ndarray, np.ndarray, dict[str, list[np.ndarray]]]:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("ROS 源需要 pandas+pyarrow：pip install pandas pyarrow") from e

    export = ep_dir / "export"
    states = pd.read_parquet(export / "states.parquet").to_numpy(dtype=np.float32)
    actions = pd.read_parquet(export / "actions.parquet").to_numpy(dtype=np.float32)
    n = len(states)
    images = {
        "front": load_images_from_dir(ep_dir / "cameras/front/frames", n),
        "wrist": load_images_from_dir(ep_dir / "cameras/wrist/frames", n),
    }
    return states, actions, images


def load_sim_episode(ep_dir: Path) -> tuple[np.ndarray, np.ndarray, dict[str, list[np.ndarray]]]:
    try:
        import h5py
    except ImportError as e:
        raise ImportError("仿真源需要 h5py：pip install h5py") from e

    h5_path = ep_dir / "rollout.hdf5"
    if not h5_path.exists():
        raise FileNotFoundError(f"Missing {h5_path}")

    with h5py.File(h5_path, "r") as f:
        states = np.asarray(f["states"], dtype=np.float32)
        actions = np.asarray(f["actions"], dtype=np.float32)
        front = np.asarray(f["images/front"], dtype=np.uint8)
        wrist = np.asarray(f["images/wrist"], dtype=np.uint8)

    images = {
        "front": [front[i] for i in range(len(states))],
        "wrist": [wrist[i] for i in range(len(states))],
    }
    return states, actions, images


def load_mp4_episode(ep_dir: Path) -> tuple[np.ndarray, np.ndarray, dict[str, list[np.ndarray]]]:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("MP4 源需要 pandas+pyarrow") from e

    export = ep_dir / "export"
    states = pd.read_parquet(export / "states.parquet").to_numpy(dtype=np.float32)
    actions = pd.read_parquet(export / "actions.parquet").to_numpy(dtype=np.float32)
    n = len(states)
    images = {
        "front": load_images_from_dir(ep_dir / "cameras/front/frames", n),
        "wrist": load_images_from_dir(ep_dir / "cameras/wrist/frames", n),
    }
    return states, actions, images


def load_episode(ep_dir: Path, source: str) -> tuple[np.ndarray, np.ndarray, dict[str, list[np.ndarray]]]:
    ep_dir = Path(ep_dir)
    if source == "ros":
        return load_ros_episode(ep_dir)
    if source == "sim":
        return load_sim_episode(ep_dir)
    if source == "mp4":
        return load_mp4_episode(ep_dir)
    raise ValueError(f"Unsupported source: {source}")
