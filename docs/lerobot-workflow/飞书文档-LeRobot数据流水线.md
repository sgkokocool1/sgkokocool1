LeRobot 数据流水线完整手册（飞书粘贴版）

使用说明：全选本文档内容 → 复制 → 飞书文档空白处粘贴。飞书会自动识别标题、表格、代码块、列表。若表格未自动转换，可选中表格区域后使用「插入 → 表格」重新格式化。

---

一、文档说明

本手册涵盖 LeRobotDataset v3.0 格式解读、本地服务器日常采集、按需构建数据集、按周/按子集训练全流程。

参考链接：
- Hugging Face 官方博客：https://huggingface.co/blog/lerobot-datasets-v3
- LeRobot 官方文档：https://huggingface.co/docs/lerobot/en/lerobot-dataset-v3

---

二、架构总览

【三层数据架构】

Layer 1  原始数据湖  /data/raw/
  - 内容：ROS bag、MP4、仿真 HDF5、manifest.jsonl
  - 原则：每天写入，长期保留，source of truth

        ↓  按需构建（周五 / 手动）

Layer 2  LeRobot v3  /data/lerobot/<name>/
  - 内容：meta/、data/*.parquet、videos/*.mp4

        ↓  训练

Layer 3  训练产物  /data/training/<run>/
  - 内容：checkpoints、train.log

【三条核心原则】

1. 日终只写 raw，不构建 LeRobot 数据集
2. 构建时 raw 只读，不复制；编码结果写入 /data/lerobot/
3. 任何写入必须以 finalize() 结束

---

三、LeRobot v3 格式速览

3.1 v2 与 v3 对比

| 维度 | v2.1 | v3.0 |
| 存储粒度 | 每个 episode 独立 parquet/mp4 | 多个 episode 拼接进同一 file-XXXX |
| episode 边界 | 由文件名隐含 | 由 meta/episodes/ 元数据显式记录 |
| 规模上限 | 数万 episode | 面向百万 episode、亿级帧 |
| Hub 访问 | 需完整下载 | 支持 StreamingLeRobotDataset 流式读取 |
| 文件系统压力 | 高 | 低（少量大文件 + chunk 分块） |

3.2 格式三大支柱

| 支柱 | 格式 | 内容 |
| meta/ 元数据 | JSON + Parquet | schema、episode 索引、统计量、任务表 |
| data/ 表格数据 | Apache Parquet | state、action、timestamp 等帧级数据 |
| videos/ 视觉数据 | MP4 | 按相机 key 分目录，多 episode 拼接 |

3.3 目录结构

/data/lerobot/my-dataset/
├── meta/
│   ├── info.json              核心 schema 与全局配置
│   ├── stats.json             归一化统计量 mean/std/min/max
│   ├── tasks.parquet          任务文本 ↔ task_index
│   └── episodes/              每个 episode 一行索引
├── data/chunk-000/file-000.parquet
└── videos/observation.images.front/chunk-000/file-000.mp4

---

四、核心概念与字段

4.1 层级概念

| 概念 | 含义 |
| Dataset | 完整 LeRobot 仓库，含 meta + data + videos |
| Episode | 一次完整任务演示，有明确起止 |
| Frame | episode 内按固定 FPS 采样的一帧，多模态时间对齐 |
| Feature | 数据 schema，如 observation.state、action |
| Chunk | 文件系统子目录，控制单目录文件数量 |
| Task | 自然语言任务描述，映射为 task_index |

4.2 索引字段（每帧自动写入，无需手动提供）

| 字段 | 含义 |
| index | 全局帧序号，dataset[i] 的 i |
| episode_index | episode 编号，从 0 开始 |
| frame_index | episode 内帧序号，每个 episode 独立从 0 计数 |
| timestamp | episode 内相对时间（秒），步长约 1/fps |
| task_index | 任务整数 ID |
| next.done | 是否为 episode 最后一帧 |

4.3 用户定义字段

| 字段 | 含义 |
| observation.state | 机器人状态（关节角、夹爪等） |
| observation.images.<name> | 相机图像，如 front、wrist |
| action | 控制指令 / 遥操作目标 |
| task | 任务文本（add_frame 时传入） |

---

五、info.json 字段详解

| 字段 | 含义 |
| codebase_version | 格式版本，当前为 "v3.0" |
| robot_type | 机器人类型，如 aloha、so101、custom_arm |
| fps | 全局采样帧率（Hz） |
| total_episodes | episode 总数 |
| total_frames | 帧总数，全局 index 范围 [0, total_frames) |
| total_tasks | 不同任务描述数量 |
| chunks_size | 每个 chunk 目录最多容纳的 episode 数 |
| splits | 数据划分，如 {"train": "0:175"} |
| data_path | 表格数据路径模板 |
| video_path | 视频路径模板，含 {video_key} |
| data_files_size_in_mb | 单个 parquet 分片目标大小（MB） |
| video_files_size_in_mb | 单个 mp4 分片目标大小（MB） |
| features | 完整特征 schema |

features 中每个特征属性：

| 属性 | 含义 |
| dtype | float32、video、bool、int64 等 |
| shape | 如 [6] 表示 6 维向量；[480,640,3] 表示 H×W×C |
| names | 各维语义名称 |
| video_info | 仅视频特征：codec、fps、是否深度图 |

---

六、manifest.jsonl 字段详解

每行一个 episode，构建前后对比示例：

构建前（第二周某行）：
{"date":"2025-07-16","session":"am_real_001","episode":"episode_007","source":"ros","task":"pick_red_block","success":true,"fps":30,"frames":122,"schema":"v1","path":"2025-07-16/am_real_001/episode_007","imported_to":null,"imported_at":null}

构建后（仅被导入的行变化）：
{"date":"2025-07-16",...,"path":"2025-07-16/am_real_001/episode_007","imported_to":"local/pick-place-w2-202507","imported_at":"2025-07-22T11:30:00+00:00"}

| 字段 | 含义 |
| date | 采集日期 YYYY-MM-DD，子集筛选靠这个 |
| path | 相对 raw 根目录路径，构建时读取文件 |
| source | ros / sim / mp4 |
| task | 任务文本 |
| success | 是否成功，false 不导入训练集 |
| imported_to | 已导入的数据集 ID，null 表示未导入 |
| imported_at | 导入时间 ISO8601 |

---

七、本地服务器物理存储

7.1 目录布局

/data/
├── raw/                          原始数据湖
│   ├── manifest.jsonl            全局 episode 索引
│   ├── schema/v1_features.json   冻结 feature 定义
│   ├── 2025-07-07/ ...           按日期归档
│   └── 2025-07-14/ ...
├── staging/today/                当日采集缓冲，日终清空
├── lerobot/                      LeRobot v3 训练格式
│   ├── pick-place-v1/            每周增量数据集
│   └── pick-place-w2-202507/     子集数据集
├── builds/                       构建日志与报告
├── training/                     checkpoint
└── scripts/                      运维脚本

7.2 单条 episode 原始格式

/data/raw/2025-07-16/am_real_001/episode_007/
├── episode_meta.json
├── export/states.parquet
├── export/actions.parquet
├── export/timestamps.parquet
└── cameras/
    ├── front/frames/000000.jpg
    └── wrist/frames/000000.jpg

episode_meta.json 模板：

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

schema v1_features.json 模板：

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

---

八、服务器初始化（一次性）

步骤 1：创建目录

sudo mkdir -p /data/{raw/schema,staging/today,lerobot,builds,training,scripts}
sudo chown -R $USER:$USER /data

步骤 2：部署脚本

cd /path/to/repo/docs/lerobot-workflow/scripts
bash deploy_to_server.sh /data
pip install -r /data/scripts/requirements.txt

步骤 3：按机器人修改 schema

编辑 /data/raw/schema/v1_features.json，采集前冻结，不要随意改 shape 和相机 key。

---

九、日常采集流程（每天）

9.1 时间线

| 时间 | 动作 | 位置 |
| 09:00–17:30 | 实机/仿真采集 | 写入 /data/staging/today/ |
| 18:30 | daily_ingest.sh 自动执行 | robot-server |
| — | 不构建 LeRobot 数据集 | — |

9.2 日终脚本做了什么

1. 校验每个 episode（validate_episode.py）
2. 追加一行到 manifest.jsonl（append_manifest.py）
3. 移动到 /data/raw/YYYY-MM-DD/session/episode_XXX/
4. 清空 staging/today/

9.3 手动触发

DATA_ROOT=/data /data/scripts/daily_ingest.sh

9.4 manifest 新增一行示例

{"date":"2025-07-16","session":"am_real_001","episode":"episode_007","source":"ros","task":"pick_red_block","success":true,"fps":30,"frames":122,"schema":"v1","path":"2025-07-16/am_real_001/episode_007","imported_to":null,"imported_at":null}

---

十、一周数据示例

10.1 一周采集明细

| 日期 | 来源 | Episodes | 成功 | 任务 |
| 周一 07-07 | ROS | 20 | 16 | pick_red_block |
| 周二 07-08 | ROS | 40 | 36 | pick_red_block |
| 周三 07-09 | ROS+仿真 | 70 | 68 | pick_red_block |
| 周四 07-10 | ROS | 35 | 27 | pick + place_in_bin |
| 周五 07-11 | ROS | 45 | 40 | pick + place |
| 周六 07-12 | MP4 | 5 | 5 | pick_red_block |
| 周日 07-13 | — | 0 | — | 仅校验 |

一周成功 episode 约 192 条（第二周子集构建示例为 175 条）。

10.2 一周时间轴

周一–周六 18:30   daily_ingest → raw/ + manifest
周五 18:45         build_weekly_dataset.sh（增量构建）
周六 09:00         train_policy.sh（训练）
周日 10:00         weekly_qc.sh（校验）

---

十一、每周构建与训练（默认流程）

适合：每周五把本周所有未导入的成功 episode 增量写入同一数据集。

11.1 周五增量构建

DATA_ROOT=/data /data/scripts/build_weekly_dataset.sh

内部流程：
筛选 manifest：success=true 且 imported_to=null
→ 数据集不存在则 create，已存在则 resume
→ build_lerobot_dataset.py → finalize()
→ 更新 manifest.imported_to = "local/pick-place-v1"

11.2 周六训练

DATASET_NAME=pick-place-v1 DATA_ROOT=/data /data/scripts/train_policy.sh

11.3 构建产物

/data/lerobot/pick-place-v1/
├── meta/info.json       total_episodes=205
├── data/
└── videos/

---

十二、子集构建：一个月只用第二周

适合：整月都在采集，但某次实验只要 07-14 ~ 07-20 的数据，新建独立数据集。

12.1 一键执行

export DATA_ROOT=/data
export DATE_FROM=2025-07-14
export DATE_TO=2025-07-20
export DATASET_NAME=pick-place-w2-202507
/data/scripts/build_subset_dataset.sh

12.2 分步执行

步骤 1：筛选第二周成功 episode

python3 /data/scripts/filter_manifest.py \
  --input  /data/raw/manifest.jsonl \
  --output /data/builds/2025-07-14_to_2025-07-20/import_list.jsonl \
  --date-from 2025-07-14 \
  --date-to 2025-07-20 \
  --success-only

步骤 2：新建数据集（create，不是 resume）

python3 /data/scripts/build_lerobot_dataset.py \
  --mode create \
  --raw-root /data/raw \
  --dataset-root /data/lerobot/pick-place-w2-202507 \
  --repo-id local/pick-place-w2-202507 \
  --schema /data/raw/schema/v1_features.json \
  --import-list /data/builds/2025-07-14_to_2025-07-20/import_list.jsonl \
  --log-dir /data/builds/2025-07-14_to_2025-07-20 \
  --streaming-encoding

步骤 3：训练

DATASET_NAME=pick-place-w2-202507 DATA_ROOT=/data /data/scripts/train_policy.sh

12.3 构建前后 manifest 变化

| 行 date | 构建前 imported_to | 构建后 imported_to |
| 2025-07-07（第一周） | null | null（不变） |
| 2025-07-16（第二周成功） | null | local/pick-place-w2-202507 |
| 2025-07-15（第二周失败） | null | null（未导入） |
| 2025-07-21（第三周） | null | null（不变） |

12.4 构建后 info.json 示例

{
  "codebase_version": "v3.0",
  "robot_type": "custom_arm",
  "fps": 30,
  "total_episodes": 175,
  "total_frames": 26250,
  "total_tasks": 2,
  "splits": { "train": "0:175" }
}

12.5 关键注意

- raw 文件不用移动、不用复制
- episode_meta.json 不用改
- 用 create 新建独立目录，不要用 resume
- 筛选靠 date 范围，不靠 imported_to=null

---

十三、向已有数据集追加数据

继续日终 ingest 后，下周五 build_weekly_dataset.sh 自动 resume。

手动 resume 示例：

python3 /data/scripts/build_lerobot_dataset.py \
  --mode resume \
  --raw-root /data/raw \
  --dataset-root /data/lerobot/pick-place-v1 \
  --repo-id local/pick-place-v1 \
  --schema /data/raw/schema/v1_features.json \
  --import-list /data/builds/2025-W29/import_list_pending.jsonl \
  --streaming-encoding

约束：schema、fps、相机 key 必须与已有数据集一致。resume 必须指定 --dataset-root 本地路径。

---

十四、cron 定时任务

写入 /etc/cron.d/robot-data：

SHELL=/bin/bash
DATA_ROOT=/data

# 周一至周六 18:30 日终归档
30 18 * * 1-6 root DATA_ROOT=/data /data/scripts/daily_ingest.sh

# 每周五 18:45 增量构建
45 18 * * 5 root DATA_ROOT=/data /data/scripts/build_weekly_dataset.sh

# 每周六 09:00 训练
0 9 * * 6 root DATA_ROOT=/data DATASET_NAME=pick-place-v1 /data/scripts/train_policy.sh

# 每周日 10:00 校验
0 10 * * 0 root DATA_ROOT=/data /data/scripts/weekly_qc.sh

# 每天 02:00 备份 raw 到 NAS
0 2 * * * root rsync -a /data/raw/ nas:/backup/robot-raw/

子集构建不加入 cron，需要时手动执行 build_subset_dataset.sh。

---

十五、三条流水线对照

| 场景 | 脚本 | 模式 |
| 每天采集归档 | daily_ingest.sh | 只写 raw + manifest |
| 每周全部未导入数据 | build_weekly_dataset.sh | create 或 resume |
| 只要某日期范围 | build_subset_dataset.sh | create 新目录 |
| 训练 | train_policy.sh | 读 /data/lerobot/<name>/ |

---

十六、快速命令索引

# 部署
bash scripts/deploy_to_server.sh /data

# 日终归档
DATA_ROOT=/data /data/scripts/daily_ingest.sh

# 每周增量构建
DATA_ROOT=/data /data/scripts/build_weekly_dataset.sh

# 只用第二周新建数据集
DATE_FROM=2025-07-14 DATE_TO=2025-07-20 DATASET_NAME=pick-place-w2-202507 DATA_ROOT=/data /data/scripts/build_subset_dataset.sh

# 训练
DATASET_NAME=pick-place-v1 DATA_ROOT=/data /data/scripts/train_policy.sh

# 周日校验
DATA_ROOT=/data /data/scripts/weekly_qc.sh

---

十七、故障排查

| 现象 | 原因 | 处理 |
| 数据集无法加载 | 未 finalize() | 重新构建，确保末尾调用 finalize() |
| resume() 报错 | 未指定 root | 加 --dataset-root /data/lerobot/xxx |
| create 报已存在 | 目录已有 info.json | 换新目录或改 --mode resume |
| 帧数不一致 | 相机与 state 未对齐 | 检查 export/ 和 cameras/ 帧数 |
| 导入了失败 episode | 未过滤 success | 加 --success-only |
| 子集混入其他周 | 用 imported_to 而非 date 筛选 | 用 filter_manifest.py --date-from/--date-to |
| lerobot 导入失败 | 未安装 | pip install -r requirements.txt |

---

十八、仓库脚本清单

| 脚本 | 用途 |
| deploy_to_server.sh | 一键部署到 /data/scripts/ |
| daily_ingest.sh | 日终归档 |
| build_weekly_dataset.sh | 每周增量构建 |
| build_subset_dataset.sh | 按日期范围新建数据集 |
| train_policy.sh | 本地训练 |
| weekly_qc.sh | 周日校验 |
| filter_manifest.py | 按日期筛选 manifest |
| build_lerobot_dataset.py | 核心构建（create/resume） |
| load_episode.py | 从 raw 加载 states/actions/images |
| append_manifest.py | 追加 manifest 行 |
| validate_episode.py | 校验单个 episode |

---

十九、一句话总结

日常采集只维护原始数据湖 + manifest 索引；需要训练时用脚本按需构建或 resume 追加 LeRobot v3 数据集；info.json 是全局契约，meta/episodes/ 是 episode 与物理文件的映射桥梁；任何写入流程都必须以 finalize() 结束。
