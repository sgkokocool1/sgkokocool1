# LeRobot 数据流水线：完整操作流程

> **一站式手册**：涵盖 LeRobot v3 格式解读、本地服务器日常采集、按需构建数据集、按周/按子集训练。  
> 理论详解见 [lerobot-dataset-v3-guide.md](../lerobot-dataset-v3-guide.md)。

---

## 目录

1. [架构总览](#1-架构总览)
2. [仓库内容](#2-仓库内容)
3. [服务器初始化](#3-服务器初始化)
4. [日常采集流程（每天）](#4-日常采集流程每天)
5. [每周构建与训练（默认流程）](#5-每周构建与训练默认流程)
6. [子集构建（如：一个月只用第二周）](#6-子集构建如一个月只用第二周)
7. [向已有数据集追加数据](#7-向已有数据集追加数据)
8. [cron 定时任务](#8-cron-定时任务)
9. [JSON 字段速查](#9-json-字段速查)
10. [故障排查](#10-故障排查)

---

## 1. 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1  原始数据湖  /data/raw/                                 │
│  ROS bag · MP4 · 仿真 HDF5 · manifest.jsonl                      │
│  ★ 每天写入，长期保留，source of truth                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ 按需构建（周五 / 手动）
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2  LeRobot v3  /data/lerobot/<name>/                      │
│  meta/ · data/*.parquet · videos/*.mp4                           │
└────────────────────────────┬────────────────────────────────────┘
                             │ 训练
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3  训练产物  /data/training/<run>/                        │
└─────────────────────────────────────────────────────────────────┘
```

**三条原则：**

1. 日终只写 raw，不构建 LeRobot 数据集
2. 构建时 raw 只读，不复制；编码结果写入 `/data/lerobot/`
3. 任何写入必须以 `finalize()` 结束

---

## 2. 仓库内容

```
docs/lerobot-workflow/
├── README.md                          ← 本文件（操作流程）
├── examples/                          ← 示例 JSON / JSONL
│   ├── schema/v1_features.json        ← feature 定义（创建数据集用）
│   ├── episode_meta.json              ← 单条 episode 元数据
│   ├── session_meta.json              ← 单次采集会话元数据
│   ├── manifest_sample.jsonl          ← 全月 manifest 节选
│   ├── import_list_week2.jsonl        ← 第二周筛选清单
│   ├── import_report.json             ← 构建报告
│   └── info_output_sample.json        ← 构建后 info.json 样例
└── scripts/                           ← 可部署到 /data/scripts/
    ├── deploy_to_server.sh            ← 一键部署
    ├── requirements.txt
    ├── daily_ingest.sh                ← 日终归档
    ├── build_weekly_dataset.sh        ← 每周增量构建
    ├── build_subset_dataset.sh        ← 按日期范围新建数据集
    ├── train_policy.sh                ← 本地训练
    ├── weekly_qc.sh                   ← 周日校验
    ├── filter_manifest.py
    ├── append_manifest.py
    ├── update_manifest_imported.py
    ├── validate_episode.py
    ├── load_episode.py
    ├── build_lerobot_dataset.py       ← 核心构建脚本
    └── weekly_qc.py
```

---

## 3. 服务器初始化

### 3.1 目录结构

在 `robot-server` 上创建：

```bash
sudo mkdir -p /data/{raw/schema,staging/today,lerobot,builds,training,scripts}
sudo chown -R $USER:$USER /data
```

最终布局：

```
/data/
├── raw/
│   ├── manifest.jsonl
│   └── schema/v1_features.json
├── staging/today/
├── lerobot/
├── builds/
├── training/
└── scripts/          ← 从本仓库部署
```

### 3.2 部署脚本与依赖

```bash
# 克隆仓库后
cd /path/to/repo/docs/lerobot-workflow/scripts
bash deploy_to_server.sh /data

pip install -r /data/scripts/requirements.txt
```

### 3.3 按机器人修改 schema

编辑 `/data/raw/schema/v1_features.json`（参考 `examples/schema/v1_features.json`）：

```json
{
  "fps": 30,
  "robot_type": "custom_arm",
  "features": {
    "observation.state": { "dtype": "float32", "shape": [6], "names": { "motors": ["j1","j2","j3","j4","j5","j6"] } },
    "action": { "dtype": "float32", "shape": [6], "names": { "motors": ["j1","j2","j3","j4","j5","j6"] } },
    "observation.images.front": { "dtype": "video", "shape": [480, 640, 3], "names": ["height","width","channel"] },
    "observation.images.wrist": { "dtype": "video", "shape": [480, 640, 3], "names": ["height","width","channel"] }
  }
}
```

> **采集前冻结 schema**，后续不要随意改 shape / 相机 key。

---

## 4. 日常采集流程（每天）

### 4.1 时间线

| 时间 | 动作 | 位置 |
|------|------|------|
| 09:00–17:30 | 实机/仿真采集 | 写入 `/data/staging/today/` |
| 18:30 | `daily_ingest.sh` 自动执行 | `robot-server` |
| — | **不构建 LeRobot 数据集** | — |

### 4.2 单条 episode 落地格式

采集时每个 episode 目录：

```
/data/staging/today/am_real_001/episode_007/
├── episode_meta.json
├── ros/recording.mcap              # 或仿真 rollout.hdf5
├── export/                         # 日终脚本生成
│   ├── states.parquet
│   ├── actions.parquet
│   └── timestamps.parquet
└── cameras/
    ├── front/frames/000000.jpg
    └── wrist/frames/000000.jpg
```

**`episode_meta.json` 模板**（参考 `examples/episode_meta.json`）：

```json
{
  "episode_id": "episode_007",
  "task": "pick_red_block",
  "success": true,
  "source": "ros",
  "fps": 30,
  "frames": 122,
  "operator": "bob",
  "robot_id": "arm_01",
  "started_at": "2025-07-16T10:23:15+08:00",
  "ended_at": "2025-07-16T10:23:19+08:00",
  "notes": ""
}
```

### 4.3 日终执行

```bash
# 手动触发
DATA_ROOT=/data /data/scripts/daily_ingest.sh
```

**日终做了什么：**

1. 校验每个 episode（`validate_episode.py`）
2. 追加一行到 `manifest.jsonl`（`append_manifest.py`）
3. 移动到 `/data/raw/YYYY-MM-DD/session/episode_XXX/`
4. 清空 `staging/today/`

**manifest 新增一行示例：**

```jsonl
{"date":"2025-07-16","session":"am_real_001","episode":"episode_007","source":"ros","task":"pick_red_block","success":true,"fps":30,"frames":122,"schema":"v1","path":"2025-07-16/am_real_001/episode_007","imported_to":null,"imported_at":null}
```

---

## 5. 每周构建与训练（默认流程）

适合：**每周五把本周所有未导入的成功 episode 增量写入同一数据集**。

### 5.1 周五 18:45 — 增量构建

```bash
DATA_ROOT=/data /data/scripts/build_weekly_dataset.sh
```

内部逻辑：

```
筛选 manifest：success=true 且 imported_to=null
    ↓
数据集不存在 → create；已存在 → resume
    ↓
build_lerobot_dataset.py → finalize()
    ↓
更新 manifest.imported_to = "local/pick-place-v1"
```

### 5.2 周六 — 训练

```bash
DATASET_NAME=pick-place-v1 DATA_ROOT=/data /data/scripts/train_policy.sh
```

### 5.3 一周示例数据量

| 日期 | Episodes | 成功 |
|------|----------|------|
| 周一–周五 | ~180 | ~155 |
| 仿真补充 | 50 | 50 |
| **本周导入** | — | **~205** |

构建产物：

```
/data/lerobot/pick-place-v1/
├── meta/info.json       total_episodes=205
├── data/
└── videos/
```

---

## 6. 子集构建（如：一个月只用第二周）

适合：**整月都在采集，但某次实验只要 07-14 ~ 07-20 的数据，新建独立数据集**。

### 6.1 执行命令

```bash
export DATA_ROOT=/data
export DATE_FROM=2025-07-14
export DATE_TO=2025-07-20
export DATASET_NAME=pick-place-w2-202507

/data/scripts/build_subset_dataset.sh
```

等价于分步执行：

```bash
# 1. 筛选
python3 /data/scripts/filter_manifest.py \
  --input  /data/raw/manifest.jsonl \
  --output /data/builds/2025-07-14_to_2025-07-20/import_list.jsonl \
  --date-from 2025-07-14 \
  --date-to 2025-07-20 \
  --success-only

# 2. 新建（create，不是 resume）
python3 /data/scripts/build_lerobot_dataset.py \
  --mode create \
  --raw-root /data/raw \
  --dataset-root /data/lerobot/pick-place-w2-202507 \
  --repo-id local/pick-place-w2-202507 \
  --schema /data/raw/schema/v1_features.json \
  --import-list /data/builds/2025-07-14_to_2025-07-20/import_list.jsonl \
  --log-dir /data/builds/2025-07-14_to_2025-07-20 \
  --streaming-encoding
```

### 6.2 构建前后 manifest 变化

| 行 date | 构建前 imported_to | 构建后 imported_to |
|---------|-------------------|-------------------|
| 2025-07-07（第一周） | null | **null**（不变） |
| 2025-07-16（第二周成功） | null | `local/pick-place-w2-202507` |
| 2025-07-15（第二周失败） | null | **null**（未导入） |
| 2025-07-21（第三周） | null | **null**（不变） |

### 6.3 训练子集数据集

```bash
DATASET_NAME=pick-place-w2-202507 DATA_ROOT=/data /data/scripts/train_policy.sh
```

---

## 7. 向已有数据集追加数据

第二周及以后，继续日终 ingest，下周五 `build_weekly_dataset.sh` 自动 `resume`：

```bash
# 手动 resume 示例
python3 /data/scripts/build_lerobot_dataset.py \
  --mode resume \
  --raw-root /data/raw \
  --dataset-root /data/lerobot/pick-place-v1 \
  --repo-id local/pick-place-v1 \
  --schema /data/raw/schema/v1_features.json \
  --import-list /data/builds/2025-W29/import_list_pending.jsonl \
  --streaming-encoding
```

**约束：** schema、fps、相机 key 必须与已有数据集一致。

---

## 8. cron 定时任务

写入 `/etc/cron.d/robot-data`：

```cron
SHELL=/bin/bash
DATA_ROOT=/data

# 周一至周六 18:30 日终归档
30 18 * * 1-6 root DATA_ROOT=/data /data/scripts/daily_ingest.sh

# 每周五 18:45 增量构建 LeRobot 数据集
45 18 * * 5 root DATA_ROOT=/data /data/scripts/build_weekly_dataset.sh

# 每周六 09:00 训练（可按需关闭改手动）
0 9 * * 6 root DATA_ROOT=/data DATASET_NAME=pick-place-v1 /data/scripts/train_policy.sh

# 每周日 10:00 校验 manifest 与 raw 一致性
0 10 * * 0 root DATA_ROOT=/data /data/scripts/weekly_qc.sh

# 每天 02:00 备份 raw 到 NAS（按需修改路径）
0 2 * * * root rsync -a /data/raw/ nas:/backup/robot-raw/
```

**子集构建**不加入 cron，需要时手动执行 `build_subset_dataset.sh`。

---

## 9. JSON 字段速查

### 9.1 manifest.jsonl（每行一个 episode）

| 字段 | 含义 |
|------|------|
| `date` | 采集日期 `YYYY-MM-DD`，**子集筛选靠这个** |
| `path` | 相对 raw 根目录的路径，构建时读取文件用 |
| `source` | `ros` / `sim` / `mp4` |
| `task` | 任务文本 |
| `success` | 是否成功，`false` 不导入训练集 |
| `imported_to` | 已导入的数据集 ID，`null` 表示未导入 |
| `imported_at` | 导入时间 ISO8601 |

### 9.2 info.json（构建后自动生成）

| 字段 | 含义 |
|------|------|
| `total_episodes` | 本数据集中 episode 数 |
| `total_frames` | 帧总数 |
| `total_tasks` | 不同任务数 |
| `fps` | 全局采样率 |
| `features` | 完整 schema |
| `data_path` / `video_path` | 分片文件路径模板 |

完整解读见 [lerobot-dataset-v3-guide.md 第 4 章](../lerobot-dataset-v3-guide.md#4-infojson-字段详解)。

---

## 10. 故障排查

| 现象 | 原因 | 处理 |
|------|------|------|
| 数据集无法加载 | 未 `finalize()` | 重新构建，确保脚本末尾调用 `finalize()` |
| `resume()` 报错 | 未指定 `root` | `--dataset-root /data/lerobot/xxx` |
| `create` 报已存在 | 目录已有 info.json | 换新 `--dataset-root` 或改 `--mode resume` |
| 帧数不一致 | 相机与 state 未对齐 | 检查 `export/` 和 `cameras/` 帧数 |
| 导入了失败 episode | 未过滤 success | 加 `--success-only` |
| 子集混入了其他周 | 用 imported_to 而非 date 筛选 | 用 `filter_manifest.py --date-from/--date-to` |
| `lerobot` 导入失败 | 未安装 | `pip install -r requirements.txt` |

---

## 快速命令索引

```bash
# 部署
bash scripts/deploy_to_server.sh /data

# 日终归档
DATA_ROOT=/data /data/scripts/daily_ingest.sh

# 每周增量构建
DATA_ROOT=/data /data/scripts/build_weekly_dataset.sh

# 只用第二周新建数据集
DATE_FROM=2025-07-14 DATE_TO=2025-07-20 DATASET_NAME=pick-place-w2-202507 \
  DATA_ROOT=/data /data/scripts/build_subset_dataset.sh

# 训练
DATASET_NAME=pick-place-v1 DATA_ROOT=/data /data/scripts/train_policy.sh

# 周日校验
DATA_ROOT=/data /data/scripts/weekly_qc.sh
```

---

## 相关文档

- [LeRobotDataset v3.0 实践指南（理论详解）](../lerobot-dataset-v3-guide.md)
- [Hugging Face 官方博客](https://huggingface.co/blog/lerobot-datasets-v3)
- [LeRobot 官方文档](https://huggingface.co/docs/lerobot/en/lerobot-dataset-v3)
