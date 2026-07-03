# 原始数据 & 资产数据：数据库 + Elasticsearch 详细设计方案

> 依据数据流水线架构图：原始数据（检测→清洗→场景标签预处理）与资产数据（审核→合成→资产标签）。  
> 代码实现：`robot-data-platform/internal/model/`（GORM）、`internal/esdoc/`（ES 文档与 Mapping）。

---

## 1. 架构总览

```
                    PostgreSQL (权威状态)              Elasticsearch (检索/聚合)
                    ─────────────────────              ──────────────────────────
采集/开源 ──► 检测 ──► raw_data (INIT)                                     
              清洗 ──► correct / anomaly          ──► raw_data_records
              预处理 ──► processing / finished         (场景标签 tags)
                    │                                      ▲
                    │ 审核                                 │ Outbox 同步
                    ▼                                      │
              asset_data (INIT)                                             
              合成 ──► success / failure          ──► asset_data_records
              打标 ──► 资产标签                          (资产标签 tags)

tag_node (树) ◄── raw_data_tag / asset_data_tag ──► 冗余 path 到 ES
```

**原则：**

| 存储 | 职责 |
|------|------|
| PostgreSQL | 事务、状态机、外键、标签树权威结构 |
| Elasticsearch | 全文检索、标签子树过滤、看板聚合 |
| Outbox | PG 提交后异步写 ES，保证最终一致 |

---

## 2. 状态机（与流程图对齐）

### 2.1 原始数据 `raw_data.status`

| 状态 | 枚举值 | 触发阶段 | 说明 |
|------|--------|----------|------|
| 初始化 | `init` | 检测程序入库 | 扫描、格式转换、写入 DB |
| 数据正确 | `correct` | 数据清洗通过 | 可进入预处理 |
| 数据异常 | `anomaly` | 数据清洗失败 | 需人工处理或丢弃 |
| 处理中 | `processing` | 打标预处理开始 | 自动打标/预处理进行中 |
| 处理完成 | `finished` | 打标预处理完成 | **场景标签写入 ES**，可进入审核 |
| 已归档 | `archived` | 冷存储 | 可选 |

### 2.2 资产数据 `asset_data.status`

| 状态 | 枚举值 | 触发阶段 | 说明 |
|------|--------|----------|------|
| 初始化 | `init` | 数据审核入库 | 从 finished 的 raw 选拔 |
| 审核中 | `auditing` | 自动/人工审核 | 可选中间态 |
| 合成中 | `processing` | 数据合成 | build LeRobot 等 |
| 成功 | `success` | 合成成功 | |
| 失败 | `failure` | 合成失败 | |
| 已发布 | `published` | 发布训练 | **资产标签写入 ES** |

---

## 3. 表一：`raw_data` 原始数据表（逐字段）

GORM 定义见 `internal/model/raw_asset.go`。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | uint64 | PK | 内部主键 |
| `uuid` | char(36) | UNIQUE, NOT NULL | 对外 ID，**ES `_id` 同源** |
| `data_type` | varchar(32) | NOT NULL, INDEX | `ros_bag`/`ros_mcap`/`mp4`/`hdf5`/`episode_dir`/`multi_modal` |
| `source_type` | varchar(32) | NOT NULL, INDEX | `collected` 采集 / `open_source` 开源 |
| `status` | varchar(32) | NOT NULL, INDEX | 状态机，见上表 |
| `status_message` | varchar(512) | | 失败原因或状态说明 |
| `prev_status` | varchar(32) | | 上一状态，审计用 |
| `name` | varchar(256) | NOT NULL, INDEX | 显示名 |
| `code` | varchar(128) | UNIQUE | 业务编码 `RAW-20250716-0007` |
| `description` | text | | 描述 |
| `storage_path` | varchar(1024) | NOT NULL, INDEX | 物理路径 `/data/raw/.../episode_007` |
| `metadata_uri` | varchar(1024) | | `episode_meta.json` 绝对路径 |
| `manifest_ref` | varchar(512) | INDEX | manifest.jsonl 的 `path` 字段 |
| `preview_uri` | varchar(1024) | | 缩略图/首帧 |
| `checksum` | char(64) | INDEX | SHA256 |
| `file_count` | int32 | | 文件数 |
| `total_bytes` | int64 | | 字节数 |
| `total_frames` | int32 | | 帧数 |
| `duration_sec` | double | | 时长 |
| `fps` | float | | 帧率 |
| `robot_id` | varchar(64) | INDEX | 机器人 |
| `operator_id` | varchar(64) | INDEX | 操作员 |
| `scene_code` | varchar(128) | INDEX | 场景编码 |
| `task_name` | varchar(256) | INDEX | 任务名 |
| `session_key` | varchar(128) | INDEX | 采集会话 |
| `episode_name` | varchar(64) | | episode 目录名 |
| `success_flag` | bool | NULL | 采集是否成功 |
| `collected_at` | timestamptz | INDEX | 采集开始 |
| `collection_end` | timestamptz | | 采集结束 |
| `detected_at` | timestamptz | | 检测入库 → INIT |
| `cleaned_at` | timestamptz | | 清洗完成 |
| `preprocessed_at` | timestamptz | | 预处理完成 → finished |
| `archived_at` | timestamptz | | 归档 |
| `extra_meta` | jsonb | | 扩展（validation 摘要等） |
| `schema_ver` | varchar(16) | default v1 | feature schema 版本 |
| `es_sync_version` | int64 | | 每次变更递增，ES 幂等 |
| `es_indexed_at` | timestamptz | | 最近同步 ES 时间 |
| `es_doc_id` | varchar(64) | INDEX | 默认 = uuid |
| `version` | int32 | | 乐观锁 |
| `created_by` / `updated_by` | varchar(64) | | 操作人 |
| `created_at` / `updated_at` | timestamptz | | |
| `deleted_at` | timestamptz | INDEX | 软删除 |

**索引建议：**

- `idx_raw_type_status (data_type, status)`
- `idx_raw_robot_scene (robot_id, scene_code)`
- `manifest_ref` 唯一业务查找

---

## 4. 表二：`asset_data` 资产数据表（逐字段）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | uint64 | PK | |
| `uuid` | char(36) | UNIQUE | ES `_id` |
| `asset_type` | varchar(32) | NOT NULL, INDEX | `lerobot_dataset`/`training_pack`/`eval_pack`/`synthetic` |
| `status` | varchar(32) | NOT NULL, INDEX | init/success/failure/... |
| `status_message` | varchar(512) | | |
| `prev_status` | varchar(32) | | |
| `name` | varchar(256) | NOT NULL | 资产名 |
| `code` | varchar(128) | UNIQUE | `ASSET-pick-place-v1` |
| `description` | text | | |
| `storage_path` | varchar(1024) | NOT NULL | `/data/lerobot/pick-place-v1` |
| `dataset_id` | varchar(256) | INDEX | `local/pick-place-v1` |
| `metadata_uri` | varchar(1024) | | `meta/info.json` 路径 |
| `output_uri` | varchar(1024) | | 训练/发布入口 |
| `checksum` | char(64) | | |
| `episode_count` | int32 | | |
| `frame_count` | int64 | | |
| `task_count` | int32 | | |
| `total_bytes` | int64 | | |
| `fps` | float | | |
| `robot_type` | varchar(64) | INDEX | |
| `synthesis_config` | jsonb | | 合成参数 `date_from`/`filter` 等 |
| `audit_result` | jsonb | | 审核结果 |
| `auditor_id` | varchar(64) | | |
| `audit_score` | float | | 0-1 |
| `parent_asset_id` | uint64 | INDEX | 增量构建父版本 |
| `build_job_id` | uint64 | INDEX | 关联批任务 |
| `audited_at` / `synthesized_at` / `published_at` | timestamptz | | 时间线 |
| `extra_meta` | jsonb | | |
| `es_sync_version` / `es_indexed_at` / `es_doc_id` | | | 同 raw |
| `version` / 审计字段 / 软删除 | | | 同 raw |

### 4.1 关联表 `asset_data_raw_source`

多原始数据 → 一资产（合成）

| 字段 | 说明 |
|------|------|
| `asset_data_id` | 资产 ID |
| `raw_data_id` | 来源 raw ID |
| `role` | primary / supplement |
| `weight` | 合成权重 |

---

## 5. 树状标签设计

### 5.1 `tag_node` 标签树表（PostgreSQL 权威）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | uint64 | PK |
| `parent_id` | uint64 NULL | 父节点，NULL=根 |
| `domain` | varchar(16) | **`raw`** 场景标签 / **`asset`** 资产标签 |
| `code` | varchar(128) | 节点编码 `kitchen` |
| `name` | varchar(256) | 显示名 `厨房` |
| `level` | int16 | 层级深度 |
| `path` | varchar(1024) UNIQUE | **物化路径** `/scene/indoor/kitchen` |
| `full_name` | varchar(512) | `场景/室内/厨房` |
| `sort_order` | int32 | 同级排序 |
| `is_leaf` | bool | 是否可绑定 |
| `is_active` | bool | 是否启用 |

**树示例（domain=raw 场景标签）：**

```
/scene                    level=0  场景
/scene/indoor             level=1  室内
/scene/indoor/kitchen     level=2  厨房        ← 叶子，可绑定
/scene/outdoor            level=1  室外
/task                     level=0  任务
/task/pick_red_block      level=1  抓红块
/quality                  level=0  质量
/quality/high             level=1  高质量
```

**树示例（domain=asset 资产标签）：**

```
/dataset                  level=0  数据集用途
/dataset/train            level=1  训练集
/dataset/eval             level=1  评测集
/experiment               level=0  实验
/experiment/exp-2025-w28    level=1  第28周实验
```

### 5.2 绑定表

| 表 | 字段 | 说明 |
|----|------|------|
| `raw_data_tag` | raw_data_id, tag_id, source, confidence | 原始数据绑场景标签 |
| `asset_data_tag` | asset_data_id, tag_id, source, confidence | 资产绑资产标签 |

`source`: `auto` 自动打标 / `manual` 人工 / `rule` 规则引擎

---

## 6. Elasticsearch：两个 Record 结构

### 6.1 索引划分

| 索引名 | 文档类型 | PG 来源 | 写入时机 |
|--------|----------|---------|----------|
| `raw_data_records` | RawDataRecord | raw_data + tags | status→finished 或标签变更 |
| `asset_data_records` | AssetDataRecord | asset_data + tags + sources | status→success/published 或标签变更 |

Mapping 文件：

- `internal/esdoc/mapping_raw_data.json`
- `internal/esdoc/mapping_asset_data.json`

### 6.2 RawDataRecord 核心字段

```json
{
  "raw_data_id": 10001,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "data_type": "episode_dir",
  "source_type": "collected",
  "status": "finished",
  "name": "pick episode 007",
  "storage_path": "/data/raw/2025-07-16/.../episode_007",
  "metadata_uri": "/data/raw/.../episode_meta.json",
  "manifest_ref": "2025-07-16/am_real_001/episode_007",
  "tags": [
    {
      "id": 12,
      "code": "kitchen",
      "name": "厨房",
      "path": "/scene/indoor/kitchen",
      "full_name": "场景/室内/厨房",
      "level": 2,
      "domain": "raw",
      "source": "auto",
      "confidence": 0.95
    }
  ],
  "tag_ids": [12, 25],
  "tag_paths": ["/scene", "/scene/indoor", "/scene/indoor/kitchen", "/task/pick_red_block"],
  "tag_codes": ["kitchen", "pick_red_block"],
  "tag_names": ["厨房", "抓红块"],
  "tag_text": "厨房 抓红块",
  "sync_version": 3
}
```

### 6.3 AssetDataRecord 核心字段

```json
{
  "asset_data_id": 2001,
  "uuid": "...",
  "asset_type": "lerobot_dataset",
  "status": "success",
  "dataset_id": "local/pick-place-w2-202507",
  "storage_path": "/data/lerobot/pick-place-w2-202507",
  "episode_count": 175,
  "frame_count": 26250,
  "source_raw_data_ids": [10001, 10002],
  "source_raw_data_uuids": ["...", "..."],
  "tags": [ { "path": "/dataset/train", "name": "训练集", "domain": "asset" } ],
  "tag_paths": ["/dataset", "/dataset/train", "/experiment/exp-2025-w28"]
}
```

### 6.4 为何同时存 `tags`(nested) 与 `tag_paths`(keyword)？

| 字段 | 用途 | 查询类型 |
|------|------|----------|
| `tags` nested | 精确多条件、confidence、source 过滤 | nested query |
| `tag_paths` keyword | **子树检索** prefix | `prefix: /scene/indoor` 命中所有子孙 |
| `tag_ids` | 精确 ID 列表 | terms query，最快 |
| `tag_text` | 用户模糊搜索 | match |
| `tag_names` | 中文标签名 | terms / match |

写入时 `BuildRawDataRecord` 会把**所有祖先 path** 冗余进 `tag_paths`，使 prefix 查询无需递归 PG。

---

## 7. 检索设计

### 7.1 看板聚合（优先 filter + aggs，不走 nested）

```json
GET raw_data_records/_search
{
  "size": 0,
  "aggs": {
    "by_source_type": { "terms": { "field": "source_type" } },
    "by_data_type": { "terms": { "field": "data_type" } },
    "by_status": { "terms": { "field": "status" } },
    "success_flag": { "terms": { "field": "success_flag" } }
  }
}
```

### 7.2 树状标签：查某节点下所有数据

```json
{ "prefix": { "tag_paths": "/scene/indoor/kitchen" } }
```

命中绑定了 `/scene/indoor/kitchen` 或其子标签 `/scene/indoor/kitchen/table_a` 的数据。

### 7.3 多标签 AND

```json
{
  "bool": {
    "must": [
      { "nested": { "path": "tags", "query": { "term": { "tags.path": "/task/pick_red_block" } } } },
      { "nested": { "path": "tags", "query": { "term": { "tags.path": "/quality/high" } } } }
    ]
  }
}
```

### 7.4 资产反查来源 raw

```json
{ "term": { "source_raw_data_ids": 10001 } }
```

### 7.5 列表页：PG + ES 分工

| 场景 | 用谁 |
|------|------|
| 主键/详情/状态变更 | PostgreSQL |
| 标签树浏览、全文搜、复杂过滤 | Elasticsearch |
| 事务写入 | PG → Outbox → ES |

---

## 8. 性能考虑

### 8.1 PostgreSQL

- 状态、类型、日期列建组合索引，看板 SQL 走 `daily_stats` 物化表（可复用 dashboard 设计）
- 标签绑定表 `(raw_data_id, tag_id)` 唯一，防重复
- 大字段 `description`/`extra_meta` 不做 ES 双向同步以外的热路径

### 8.2 Elasticsearch

| 配置 | 建议 | 原因 |
|------|------|------|
| `refresh_interval` | 5s | 看板近实时，非秒级强一致 |
| `number_of_shards` | raw:3, asset:2 | 按数据量调整 |
| nested `tags` | 仅精确查询用 | nested 贵，聚合用扁平 `tag_codes` |
| `tag_paths` 冗余祖先 | 写入时计算 | 避免查询时递归 |
| Bulk 写入 | 500 条/批 | Outbox 消费者 bulk index |
| `_id` = uuid | 幂等 upsert | 重试安全 |

### 8.3 同步策略（Outbox）

```
1. 业务事务：更新 raw_data + raw_data_tag + INSERT es_sync_outbox
2. COMMIT
3. 异步 worker 读 outbox pending → bulk index ES → 更新 es_indexed_at
4. 失败指数退避，retry_count < 5
```

避免「双写」不一致；ES 落后 PG 最多数秒可接受。

### 8.4 标签树变更

- 修改 `tag_node.path` 时：批量刷新受影响 raw/asset 的 ES 文档（按 tag_id terms 查 ES 再更新）
- 树深度建议 ≤ 5，path 长度 ≤ 1024

---

## 9. 流水线阶段日志 `processing_log`

| 字段 | 说明 |
|------|------|
| `stage` | detect / clean / preprocess / audit / synthesize / tag |
| `raw_data_id` / `asset_data_id` | 关联实体 |
| `status` | running / success / failed |
| `input_json` / `output_json` | 阶段输入输出 |
| `duration_ms` | 耗时 |

用于看板「任务流成功失败」统计，与图中各阶段任务一一对应。

---

## 10. 代码文件索引

```
robot-data-platform/
├── go.mod
├── internal/
│   ├── model/
│   │   ├── enums.go          # 枚举：状态、类型、标签域
│   │   ├── raw_asset.go      # raw_data, asset_data, processing_log
│   │   └── tag.go            # tag_node, 绑定表, es_sync_outbox
│   └── esdoc/
│       ├── document.go       # RawDataRecord, AssetDataRecord
│       ├── builder.go        # PG → ES 文档构建
│       ├── mapping_raw_data.json
│       ├── mapping_asset_data.json
│       └── queries.go        # DSL 示例
└── docs/
    └── raw-asset-es-design.md  # 本文档
```

### GORM 自动迁移示例

```go
db.AutoMigrate(
    &model.RawData{},
    &model.AssetData{},
    &model.AssetDataRawSource{},
    &model.TagNode{},
    &model.RawDataTag{},
    &model.AssetDataTag{},
    &model.ProcessingLog{},
    &model.ESSyncOutbox{},
)
```

---

## 11. 与现有 manifest 流水线映射

| manifest / episode | raw_data 字段 |
|------------------|---------------|
| `path` | `manifest_ref` + `storage_path` |
| `source` | `data_type` / `source_type` |
| `success` | `success_flag` |
| `task` | `task_name` |
| `imported_to` | 资产合成后写入 `asset_data.dataset_id` |

 ingest 完成 → 插入 `raw_data` status=init → 清洗 → correct → 预处理打场景标签 → finished → 同步 `raw_data_records`。

 build 完成 → 插入 `asset_data` status=success → 打资产标签 → 同步 `asset_data_records`。

---

## 12. ER 图

```
tag_node (树, domain=raw|asset)
    ▲                    ▲
    │ raw_data_tag       │ asset_data_tag
    │                    │
raw_data ──► asset_data_raw_source ──► asset_data
    │                                        │
    └──────── processing_log ◄───────────────┘
                    │
              es_sync_outbox ──► Elasticsearch
```
