# 机器人原始数据 · 处理流水线统计大看板设计方案

> 面向本地服务器 `/data/raw` + LeRobot 构建流水线的**数据统计与可视化**方案。  
> 与现有 [操作流程](./README.md)、[manifest.jsonl](./README.md#九json-字段速查) 体系对齐。

---

## 目录

1. [目标与范围](#1-目标与范围)
2. [统计指标体系](#2-统计指标体系)
3. [数据库设计](#3-数据库设计)
4. [数据同步方案](#4-数据同步方案)
5. [后端 API 设计](#5-后端-api-设计)
6. [前端 UI 设计](#6-前端-ui-设计)
7. [页面线框与组件](#7-页面线框与组件)
8. [部署架构](#8-部署架构)
9. [实施路线](#9-实施路线)
10. [附录：示例 SQL 与 JSON](#10-附录示例-sql-与-json)

---

## 1. 目标与范围

### 1.1 要回答的问题

| 问题 | 对应看板模块 |
|------|-------------|
| 现在有多少原始数据？按类型（ROS/仿真/MP4）各占多少？ | 数据分布 |
| 多少已日终归档（ingest）？多少还在 staging？ | 处理漏斗 |
| 多少已构建进 LeRobot 数据集？多少 pending？ | 数据集状态 |
| 跑了多少次处理任务流？每次成功失败多少？ | 任务流历史 |
| 按任务（pick/place）成功失败比例？ | 任务质量 |
| 按日期/操作员/机器人的趋势？ | 趋势图 |
| 磁盘占用多少？各层（raw/lerobot/training）？ | 存储概览 |

### 1.2 不在本期范围（可二期）

- 实时视频预览
- 分布式多机房汇总
- 权限细粒度 RBAC（一期仅管理员/只读）

### 1.3 设计原则

1. **manifest.jsonl 仍是 source of truth**，数据库为统计索引层，可随时从 raw 重建
2. **episode 级 + job 级** 双层统计：单条轨迹质量 vs 批处理任务结果
3. **物化日汇总表**加速看板，明细表支撑下钻
4. 与现有 shell/python 脚本通过**钩子写库**或**定时扫描**集成，不改动核心 ingest 逻辑

---

## 2. 统计指标体系

### 2.1 维度（Dimensions）

| 维度 | 字段来源 | 用途 |
|------|----------|------|
| 日期 | manifest.date | 趋势、筛选 |
| 数据来源 | manifest.source | ros / sim / mp4 / other |
| 任务 | manifest.task | pick_red_block 等 |
| 采集会话 | manifest.session | 按场次分析 |
| 操作员 | episode_meta.operator | 质量归因 |
| 机器人 | episode_meta.robot_id | 设备维度 |
| 处理阶段 | 系统计算 | staging / raw / imported / failed_validation |
| 目标数据集 | manifest.imported_to | 是否进入训练集 |
| 任务流类型 | processing_jobs.job_type | daily_ingest / build_weekly / build_subset / train |

### 2.2 指标（Metrics）

#### Episode 级

| 指标 | 计算方式 |
|------|----------|
| 原始 episode 总数 | count(episodes) |
| 成功 episode 数 | count(success=true) |
| 失败 episode 数 | count(success=false) |
| 成功率 | 成功 / 总数 |
| 总帧数 | sum(frames) |
| 已导入训练集 episode | imported_to IS NOT NULL |
| 待处理 episode | success=true AND imported_to IS NULL |
| 按来源分布 | group by source |
| 按任务分布 | group by task |

#### Job 级（任务流）

| 指标 | 计算方式 |
|------|----------|
| 任务流执行次数 | count(processing_jobs) |
| 成功任务流 | status=success |
| 失败任务流 | status=failed |
| 单次导入 episode 数 | job_episodes 关联计数 |
| 单次耗时 | finished_at - started_at |
| 跳过/失败 episode 数 | job 日志解析或 job_episodes.status |

#### 存储级

| 指标 | 计算方式 |
|------|----------|
| raw 磁盘占用 | 扫描 /data/raw |
| lerobot 磁盘占用 | 扫描 /data/lerobot |
| staging 待处理 | staging/today episode 数 |

### 2.3 处理阶段状态机（Episode）

```
[采集中] staging
    ↓ daily_ingest
[已归档] raw_archived          ← 在 manifest 中
    ↓ validate 失败
[校验失败] validation_failed
    ↓ build 选中
[构建中] building
    ↓ finalize
[已入数据集] imported            ← imported_to 非空
    ↓
[可训练] trainable
```

---

## 3. 数据库设计

推荐 **PostgreSQL 15+**（本地 `robot-server` Docker 部署），便于 JSONB、时间序列聚合、物化视图。

### 3.1 ER 关系

```
sessions 1───N episodes
episodes N───N processing_jobs  (via job_episodes)
datasets 1───N episodes         (via imported_to)
daily_stats (物化汇总，按 date+维度)
storage_snapshots (磁盘快照，按时间)
```

### 3.2 表结构

#### `sessions` — 采集会话

```sql
CREATE TABLE sessions (
    id              BIGSERIAL PRIMARY KEY,
    session_key     VARCHAR(128) NOT NULL,          -- am_real_001
    collect_date    DATE NOT NULL,
    operator        VARCHAR(64),
    robot_id        VARCHAR(64),
    environment     VARCHAR(128),
    source          VARCHAR(32),                    -- 主来源 ros/sim
    schema_version  VARCHAR(16) DEFAULT 'v1',
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (collect_date, session_key)
);
```

#### `episodes` — 核心事实表（与 manifest 同步）

```sql
CREATE TYPE episode_stage AS ENUM (
    'staging', 'raw_archived', 'validation_failed',
    'pending_import', 'imported', 'skipped'
);

CREATE TABLE episodes (
    id              BIGSERIAL PRIMARY KEY,
    path            VARCHAR(512) NOT NULL UNIQUE,   -- 2025-07-16/am_real_001/episode_007
    collect_date    DATE NOT NULL,
    session_key     VARCHAR(128) NOT NULL,
    episode_name    VARCHAR(64) NOT NULL,
    source          VARCHAR(32) NOT NULL,             -- ros | sim | mp4
    task            VARCHAR(256) NOT NULL,
    success         BOOLEAN NOT NULL,
    fps             SMALLINT NOT NULL,
    frames          INTEGER NOT NULL,
    duration_sec    REAL,
    operator        VARCHAR(64),
    robot_id        VARCHAR(64),
    stage           episode_stage NOT NULL DEFAULT 'raw_archived',
    imported_to     VARCHAR(256),                     -- local/pick-place-v1
    imported_at     TIMESTAMPTZ,
    validation_ok   BOOLEAN,
    validation_errors JSONB,
    disk_bytes      BIGINT,                           -- 可选：episode 目录大小
    meta_json       JSONB,                            -- episode_meta 全文
    first_seen_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_episodes_date ON episodes(collect_date);
CREATE INDEX idx_episodes_source ON episodes(source);
CREATE INDEX idx_episodes_task ON episodes(task);
CREATE INDEX idx_episodes_success ON episodes(success);
CREATE INDEX idx_episodes_stage ON episodes(stage);
CREATE INDEX idx_episodes_imported ON episodes(imported_to);
```

#### `datasets` — LeRobot 数据集注册

```sql
CREATE TABLE datasets (
    id              BIGSERIAL PRIMARY KEY,
    dataset_id      VARCHAR(256) NOT NULL UNIQUE,     -- local/pick-place-w2-202507
    root_path       VARCHAR(512) NOT NULL,
    total_episodes  INTEGER,
    total_frames    INTEGER,
    total_tasks     INTEGER,
    fps             SMALLINT,
    robot_type      VARCHAR(64),
    codebase_version VARCHAR(16),
    info_json       JSONB,
    built_at        TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `processing_jobs` — 任务流执行记录

```sql
CREATE TYPE job_type AS ENUM (
    'daily_ingest', 'build_weekly', 'build_subset',
    'build_create', 'build_resume', 'train', 'weekly_qc'
);

CREATE TYPE job_status AS ENUM (
    'running', 'success', 'failed', 'partial'
);

CREATE TABLE processing_jobs (
    id              BIGSERIAL PRIMARY KEY,
    job_type        job_type NOT NULL,
    status          job_status NOT NULL DEFAULT 'running',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    duration_sec    REAL,
    triggered_by    VARCHAR(64) DEFAULT 'cron',       -- cron | manual | api
    params_json     JSONB,                            -- date_from, dataset_name 等
    report_json     JSONB,                            -- import_report 全文
    log_path        VARCHAR(512),
    error_message   TEXT,
    episodes_in     INTEGER DEFAULT 0,
    episodes_ok     INTEGER DEFAULT 0,
    episodes_fail   INTEGER DEFAULT 0,
    frames_in       INTEGER DEFAULT 0
);

CREATE INDEX idx_jobs_type ON processing_jobs(job_type);
CREATE INDEX idx_jobs_status ON processing_jobs(status);
CREATE INDEX idx_jobs_started ON processing_jobs(started_at);
```

#### `job_episodes` — 任务与 episode 关联

```sql
CREATE TYPE job_ep_action AS ENUM ('ingest', 'import', 'skip', 'fail');

CREATE TABLE job_episodes (
    job_id          BIGINT NOT NULL REFERENCES processing_jobs(id) ON DELETE CASCADE,
    episode_id      BIGINT NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
    action          job_ep_action NOT NULL,
    message         TEXT,
    PRIMARY KEY (job_id, episode_id)
);
```

#### `daily_stats` — 日汇总（物化，看板主查表）

```sql
CREATE TABLE daily_stats (
    stat_date       DATE NOT NULL,
    source          VARCHAR(32) NOT NULL DEFAULT '_all',
    task            VARCHAR(256) NOT NULL DEFAULT '_all',
    -- episode 指标
    episodes_total      INTEGER NOT NULL DEFAULT 0,
    episodes_success    INTEGER NOT NULL DEFAULT 0,
    episodes_failed     INTEGER NOT NULL DEFAULT 0,
    frames_total        BIGINT NOT NULL DEFAULT 0,
    episodes_imported   INTEGER NOT NULL DEFAULT 0,
    episodes_pending    INTEGER NOT NULL DEFAULT 0,
    -- job 指标
    jobs_total          INTEGER NOT NULL DEFAULT 0,
    jobs_success        INTEGER NOT NULL DEFAULT 0,
    jobs_failed         INTEGER NOT NULL DEFAULT 0,
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (stat_date, source, task)
);
```

#### `storage_snapshots` — 磁盘快照

```sql
CREATE TABLE storage_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    snapshot_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_bytes       BIGINT,
    staging_bytes   BIGINT,
    lerobot_bytes   BIGINT,
    training_bytes  BIGINT,
    builds_bytes    BIGINT,
    details_json    JSONB                             -- 按子目录明细
);
```

### 3.3 物化视图（可选，加速总览）

```sql
CREATE MATERIALIZED VIEW mv_overview AS
SELECT
    COUNT(*)                                    AS episodes_total,
    COUNT(*) FILTER (WHERE success)             AS episodes_success,
    COUNT(*) FILTER (WHERE NOT success)         AS episodes_failed,
    COUNT(*) FILTER (WHERE imported_to IS NOT NULL) AS episodes_imported,
    COUNT(*) FILTER (WHERE success AND imported_to IS NULL) AS episodes_pending,
    SUM(frames)                                 AS frames_total,
    COUNT(DISTINCT source)                      AS source_types,
    COUNT(DISTINCT task)                        AS task_types
FROM episodes;

-- 定时 REFRESH MATERIALIZED VIEW mv_overview;
```

---

## 4. 数据同步方案

### 4.1 同步来源

| 来源 | 触发时机 | 写入表 |
|------|----------|--------|
| manifest.jsonl | 日终 ingest 后 / 每 5min 扫描 | episodes |
| episode_meta.json | 同上 | episodes.meta_json |
| import_report.json | build 完成后 | processing_jobs + episodes.imported_* |
| info.json | build 完成后 | datasets |
| du/scan 脚本 | 每小时 | storage_snapshots |
| staging 目录扫描 | 每 5min | episodes.stage=staging |

### 4.2 同步脚本 `sync_stats_db.py`（伪代码）

```python
# 1. 增量读 manifest：对比 mtime 或记录 last_line_offset
for rec in read_manifest_since_checkpoint():
    upsert_episode(
        path=rec["path"],
        collect_date=rec["date"],
        source=rec["source"],
        task=rec["task"],
        success=rec["success"],
        frames=rec["frames"],
        imported_to=rec.get("imported_to"),
        imported_at=rec.get("imported_at"),
        stage=compute_stage(rec),
    )

# 2. 扫描 staging
for ep in scan_staging("/data/staging/today"):
    upsert_episode(..., stage="staging")

# 3. 重建 daily_stats
rebuild_daily_stats(date_range=last_90_days)

# 4. 磁盘快照
insert_storage_snapshot(scan_disk("/data"))
```

### 4.3 与现有脚本集成（钩子）

在 `daily_ingest.sh` / `build_lerobot_dataset.py` 末尾追加：

```bash
python3 /data/scripts/sync_stats_db.py --event ingest --log-dir "$LOG_DIR"
```

```python
# build_lerobot_dataset.py 结束时
record_processing_job(
    job_type="build_create" if mode == "create" else "build_resume",
    status="success",
    report=report,
    episode_paths=imported_paths,
)
sync_stats_db.refresh_daily_stats()
```

### 4.4 stage 计算规则

```python
def compute_stage(rec, staging_paths, validation_cache):
    if rec["path"] in staging_paths:
        return "staging"
    if not validation_cache.get(rec["path"], True):
        return "validation_failed"
    if rec.get("imported_to"):
        return "imported"
    if rec.get("success"):
        return "pending_import"
    return "raw_archived"  # 失败但已归档
```

---

## 5. 后端 API 设计

技术栈建议：**FastAPI + SQLAlchemy + PostgreSQL**，部署在 `robot-server:8080`（内网）。

### 5.1 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/overview` | 总览 KPI |
| GET | `/api/v1/distribution/source` | 按来源分布 |
| GET | `/api/v1/distribution/task` | 按任务分布 |
| GET | `/api/v1/funnel` | 处理漏斗 |
| GET | `/api/v1/trend/daily` | 日趋势 ?from=&to= |
| GET | `/api/v1/jobs` | 任务流列表 ?type=&status= |
| GET | `/api/v1/jobs/{id}` | 任务详情 |
| GET | `/api/v1/episodes` | episode 分页列表 ?source=&success=&stage= |
| GET | `/api/v1/datasets` | 数据集列表 |
| GET | `/api/v1/storage` | 最新磁盘快照 + 趋势 |
| POST | `/api/v1/sync/trigger` | 手动触发同步（管理员） |

### 5.2 响应示例

**GET `/api/v1/overview`**

```json
{
  "episodes": {
    "total": 2150,
    "success": 1920,
    "failed": 230,
    "success_rate": 0.893,
    "imported": 1205,
    "pending": 715,
    "frames_total": 322500
  },
  "by_source": {
    "ros": { "total": 1550, "success": 1380, "imported": 900 },
    "sim": { "total": 500, "success": 500, "imported": 280 },
    "mp4": { "total": 100, "success": 40, "imported": 25 }
  },
  "jobs_7d": {
    "total": 12,
    "success": 11,
    "failed": 1
  },
  "storage": {
    "raw_gb": 420.5,
    "lerobot_gb": 180.2,
    "staging_gb": 2.1
  },
  "updated_at": "2025-07-22T12:00:00+08:00"
}
```

**GET `/api/v1/funnel`**

```json
{
  "stages": [
    { "name": "staging", "label": "待日终归档", "count": 15 },
    { "name": "raw_archived", "label": "已归档 raw", "count": 2150 },
    { "name": "pending_import", "label": "待构建导入", "count": 715 },
    { "name": "imported", "label": "已入数据集", "count": 1205 },
    { "name": "validation_failed", "label": "校验失败", "count": 18 }
  ]
}
```

---

## 6. 前端 UI 设计

### 6.1 技术栈建议

| 层级 | 选型 | 理由 |
|------|------|------|
| 框架 | React 18 + TypeScript | 生态成熟 |
| UI 库 | Ant Design 5 或 Arco Design | 后台看板组件全 |
| 图表 | ECharts 或 Apache ECharts | 漏斗图、饼图、趋势 |
| 状态 | TanStack Query | API 缓存与轮询 |
| 构建 | Vite | 轻量快速 |

访问方式：内网 `http://robot-server:3000`，一期不做公网暴露。

### 6.2 信息架构（页面）

```
/data-dashboard
├── /overview          总览大看板（默认首页）
├── /distribution      数据分布详情
├── /pipeline          处理漏斗 & 任务流
├── /episodes          Episode 明细表（可筛选导出）
├── /datasets          数据集 & 构建历史
└── /storage           存储占用
```

### 6.3 总览页布局（Overview）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  机器人数据大看板                    [日期范围 ▼] [刷新] [手动同步]  最后更新 12:00 │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│ │ 原始总数  │ │ 成功     │ │ 失败     │ │ 已入数据集 │ │ 待处理   │         │
│ │  2,150   │ │  1,920   │ │   230    │ │  1,205   │ │   715    │         │
│ │          │ │ 89.3%    │ │ 10.7%    │ │  62.7%   │ │  33.2%   │         │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
├──────────────────────────────┬──────────────────────────────────────────────┤
│  数据来源分布（饼图）          │  处理漏斗（漏斗图）                            │
│  ROS 72%  仿真 23%  MP4 5%   │  staging → raw → pending → imported         │
├──────────────────────────────┼──────────────────────────────────────────────┤
│  日采集趋势（折线）            │  任务流执行（近 7 天柱状）                      │
│  成功/失败/导入 三线           │  ingest / build / train                       │
├──────────────────────────────┴──────────────────────────────────────────────┤
│  存储占用                                                                    │
│  raw 420GB ████████████  lerobot 180GB █████  staging 2GB                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  最近任务流                                                                   │
│  类型        状态    开始时间           导入/跳过/失败    耗时                  │
│  build_weekly ✓     07-19 18:45       205 / 0 / 23      42min               │
│  daily_ingest ✓     07-19 18:30       38 / 0 / 2        3min                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.4 色彩与状态规范

| 语义 | 颜色 | 用于 |
|------|------|------|
| 成功 | `#52c41a` | 成功 episode、job success |
| 失败 | `#ff4d4f` | 失败 episode、job failed |
| 待处理 | `#faad14` | pending、staging |
| 已导入 | `#1677ff` | imported |
| 中性 | `#8c8c8c` | 总数、辅助文字 |

### 6.5 交互说明

| 交互 | 行为 |
|------|------|
| 点击 KPI 卡片 | 跳转 episodes 页并带筛选 |
| 点击饼图扇区 | 按 source 筛选分布页 |
| 点击漏斗层 | 筛选对应 stage 的 episode 列表 |
| 日期范围 | 全局过滤，默认近 30 天 |
| 自动刷新 | 每 60s 轮询 overview（可关闭） |
| 导出台账 | episodes 页支持 CSV 导出 |

---

## 7. 页面线框与组件

### 7.1 组件树

```
App
├── Layout (侧边栏 + 顶栏)
│   ├── Sider: 导航菜单
│   └── Header: 日期筛选、刷新、用户
└── Routes
    ├── OverviewPage
    │   ├── KpiCardGroup (5)
    │   ├── SourcePieChart
    │   ├── PipelineFunnelChart
    │   ├── DailyTrendChart
    │   ├── JobBarChart
    │   ├── StorageBar
    │   └── RecentJobsTable
    ├── DistributionPage
    │   ├── SourceTable + TaskTable
    │   └── StackedBarChart (date × source)
    ├── PipelinePage
    │   ├── FunnelDetail
    │   └── JobsTable (分页)
    ├── EpisodesPage
    │   ├── FilterForm
    │   └── EpisodeTable (分页、排序)
    ├── DatasetsPage
    │   ├── DatasetCards
    │   └── BuildHistoryTable
    └── StoragePage
        ├── StorageTrendChart
        └── DirectoryTreeTable
```

### 7.2 Episodes 明细表字段

| 列 | 说明 |
|----|------|
| 日期 | collect_date |
| 路径 | path（可点击打开目录提示） |
| 来源 | source 标签 |
| 任务 | task |
| 成功 | ✓/✗ |
| 帧数 | frames |
| 阶段 | stage 标签色 |
| 导入至 | imported_to |
| 操作员 | operator |
| 校验 | validation_ok |

### 7.3 任务流页 Jobs 表字段

| 列 | 说明 |
|----|------|
| ID | job id |
| 类型 | daily_ingest / build_weekly 等 |
| 状态 | success / failed / partial |
| 开始时间 | started_at |
| 耗时 | duration |
| 导入 | episodes_ok |
| 跳过 | episodes_in - episodes_ok - episodes_fail |
| 失败 | episodes_fail |
| 日志 | 链接 log_path |

---

## 8. 部署架构

```
┌──────────────── robot-server (192.168.1.100) ─────────────────┐
│                                                               │
│  /data/raw  /data/lerobot  /data/staging                      │
│         │                                                     │
│         ▼ sync_stats_db.py (cron */5 * * * *)                 │
│  ┌─────────────┐      ┌──────────────┐      ┌───────────────┐ │
│  │ PostgreSQL  │◄─────│ FastAPI      │◄─────│ React 前端    │ │
│  │  :5432      │      │  :8080       │      │  :3000 (nginx)│ │
│  └─────────────┘      └──────────────┘      └───────────────┘ │
│                                                               │
│  现有脚本：daily_ingest / build_* / train  （写库钩子）         │
└───────────────────────────────────────────────────────────────┘
```

### 8.1 Docker Compose 骨架

```yaml
# /data/dashboard/docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: robot_stats
      POSTGRES_USER: robot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - /data/dashboard/pgdata:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"

  api:
    build: ./api
    environment:
      DATABASE_URL: postgresql://robot:${DB_PASSWORD}@db:5432/robot_stats
      DATA_ROOT: /data
    volumes:
      - /data:/data:ro
    ports:
      - "127.0.0.1:8080:8080"
    depends_on:
      - db

  web:
    build: ./web
    ports:
      - "127.0.0.1:3000:80"
    depends_on:
      - api
```

---

## 9. 实施路线

### Phase 1 — 统计可查（1–2 周）

- [ ] 建表 + `sync_stats_db.py` 从 manifest 同步
- [ ] ingest/build 脚本加 job 写库钩子
- [ ] FastAPI overview / distribution / jobs 接口
- [ ] 前端 Overview 单页 + KPI + 两张图

### Phase 2 — 可下钻（1 周）

- [ ] Episodes 明细表 + 筛选导出
- [ ] Pipeline 漏斗页 + Jobs 详情
- [ ] 磁盘 storage 扫描

### Phase 3 — 完善（按需）

- [ ] Datasets 页对接 info.json
- [ ] 告警：日终失败、磁盘 > 阈值
- [ ] 操作员/机器人维度报表

---

## 10. 附录：示例 SQL 与 JSON

### 10.1 按来源统计

```sql
SELECT
    source,
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE success) AS success_cnt,
    COUNT(*) FILTER (WHERE NOT success) AS fail_cnt,
    COUNT(*) FILTER (WHERE imported_to IS NOT NULL) AS imported_cnt,
    SUM(frames) AS frames
FROM episodes
WHERE collect_date BETWEEN '2025-07-01' AND '2025-07-31'
GROUP BY source
ORDER BY total DESC;
```

### 10.2 任务流成功率（近 7 天）

```sql
SELECT
    job_type,
    COUNT(*) AS runs,
    COUNT(*) FILTER (WHERE status = 'success') AS ok,
    COUNT(*) FILTER (WHERE status = 'failed') AS fail,
    ROUND(AVG(duration_sec)::numeric, 1) AS avg_sec
FROM processing_jobs
WHERE started_at >= NOW() - INTERVAL '7 days'
GROUP BY job_type;
```

### 10.3 日趋势写入 daily_stats

```sql
INSERT INTO daily_stats (
    stat_date, source, task,
    episodes_total, episodes_success, episodes_failed,
    frames_total, episodes_imported, episodes_pending
)
SELECT
    collect_date,
    source,
    '_all',
    COUNT(*),
    COUNT(*) FILTER (WHERE success),
    COUNT(*) FILTER (WHERE NOT success),
    COALESCE(SUM(frames), 0),
    COUNT(*) FILTER (WHERE imported_to IS NOT NULL),
    COUNT(*) FILTER (WHERE success AND imported_to IS NULL)
FROM episodes
WHERE collect_date = CURRENT_DATE - 1
GROUP BY collect_date, source
ON CONFLICT (stat_date, source, task) DO UPDATE SET
    episodes_total = EXCLUDED.episodes_total,
    episodes_success = EXCLUDED.episodes_success,
    episodes_failed = EXCLUDED.episodes_failed,
    frames_total = EXCLUDED.frames_total,
    episodes_imported = EXCLUDED.episodes_imported,
    episodes_pending = EXCLUDED.episodes_pending,
    updated_at = NOW();
```

### 10.4 processing_jobs 写入示例（build 完成）

```json
{
  "job_type": "build_subset",
  "status": "success",
  "started_at": "2025-07-22T11:00:00+08:00",
  "finished_at": "2025-07-22T11:42:00+08:00",
  "duration_sec": 2520,
  "triggered_by": "manual",
  "params_json": {
    "date_from": "2025-07-14",
    "date_to": "2025-07-20",
    "dataset_name": "pick-place-w2-202507",
    "mode": "create"
  },
  "report_json": {
    "imported_episodes": 175,
    "skipped_in_range": 23,
    "total_frames": 26250,
    "by_source": { "ros": 130, "sim": 40, "mp4": 5 }
  },
  "episodes_in": 175,
  "episodes_ok": 175,
  "episodes_fail": 0,
  "frames_in": 26250
}
```

---

## 相关文档

- [数据流水线操作流程](./README.md)
- [飞书粘贴版手册](./飞书文档-LeRobot数据流水线.md)
- [LeRobot v3 实践指南](../lerobot-dataset-v3-guide.md)
