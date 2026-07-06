-- 机器人数据平台 · TiDB DDL（路径管理库）
-- 设计文档：docs/robot-data-platform/DESIGN.md
-- 原则：TiDB 只登记路径与流水线状态；标签仅存 ES

-- ============================================================
-- 1. raw_data 原始数据路径登记表
-- ============================================================

CREATE TABLE raw_data (
    id              BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    uuid            CHAR(36) NOT NULL,
    storage_path    VARCHAR(1024) NOT NULL COMMENT '物理根路径，管理主键',
    manifest_ref    VARCHAR(512) DEFAULT NULL COMMENT 'manifest.jsonl 的 path',
    metadata_uri    VARCHAR(1024) DEFAULT NULL COMMENT 'episode_meta.json 等元数据路径',
    status          VARCHAR(32) NOT NULL DEFAULT 'init' COMMENT 'init/correct/anomaly/processing/finished/archived',
    data_type       VARCHAR(32) NOT NULL DEFAULT 'episode_dir' COMMENT 'ros_bag/episode_dir/mp4/...',
    source_type     VARCHAR(32) NOT NULL DEFAULT 'collected' COMMENT 'collected/open_source/simulation',
    es_sync_version BIGINT NOT NULL DEFAULT 0,
    es_indexed_at   DATETIME DEFAULT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_raw_uuid (uuid),
    UNIQUE KEY uk_raw_storage_path (storage_path),
    KEY idx_raw_manifest_ref (manifest_ref),
    KEY idx_raw_status (status),
    KEY idx_raw_type_status (data_type, status)
) COMMENT='原始数据路径登记';

-- ============================================================
-- 2. asset_data 资产路径登记表
-- ============================================================

CREATE TABLE asset_data (
    id              BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    uuid            CHAR(36) NOT NULL,
    storage_path    VARCHAR(1024) NOT NULL COMMENT '资产根路径 /data/lerobot/...',
    dataset_id      VARCHAR(256) DEFAULT NULL COMMENT '逻辑数据集路径 local/pick-place-v1',
    metadata_uri    VARCHAR(1024) DEFAULT NULL COMMENT 'meta/info.json 路径',
    status          VARCHAR(32) NOT NULL DEFAULT 'init' COMMENT 'init/processing/success/failure/published',
    asset_type      VARCHAR(32) NOT NULL DEFAULT 'lerobot_dataset',
    es_sync_version BIGINT NOT NULL DEFAULT 0,
    es_indexed_at   DATETIME DEFAULT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_asset_uuid (uuid),
    UNIQUE KEY uk_asset_storage_path (storage_path),
    KEY idx_asset_dataset_id (dataset_id),
    KEY idx_asset_status (status),
    KEY idx_asset_type_status (asset_type, status)
) COMMENT='资产路径登记';

-- ============================================================
-- 3. asset_raw_link 资产 ← 原始数据 路径血缘（仅存路径关联）
-- ============================================================

CREATE TABLE asset_raw_link (
    id                  BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    asset_id            BIGINT NOT NULL,
    raw_id              BIGINT NOT NULL,
    raw_storage_path    VARCHAR(1024) NOT NULL COMMENT '冗余原始路径，便于按路径反查',
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_asset_raw (asset_id, raw_id),
    KEY idx_link_raw_path (raw_storage_path),
    KEY idx_link_raw_id (raw_id),
    CONSTRAINT fk_link_asset FOREIGN KEY (asset_id) REFERENCES asset_data(id),
    CONSTRAINT fk_link_raw FOREIGN KEY (raw_id) REFERENCES raw_data(id)
) COMMENT='资产与原始数据路径血缘';

-- ============================================================
-- 4. es_sync_outbox ES 同步队列（TiDB → ES）
-- ============================================================

CREATE TABLE es_sync_outbox (
    id              BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    entity_type     VARCHAR(32) NOT NULL COMMENT 'raw_data / asset_data',
    entity_id       BIGINT NOT NULL,
    entity_uuid     CHAR(36) NOT NULL,
    storage_path    VARCHAR(1024) NOT NULL COMMENT '路径，Worker 定位磁盘元数据',
    op              VARCHAR(16) NOT NULL COMMENT 'index / update / delete',
    payload         JSON DEFAULT NULL COMMENT '可选：预组装的 ES 文档；为空则由 Worker 从路径读元数据拼装',
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    retry_count     INT NOT NULL DEFAULT 0,
    last_error      TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at    DATETIME DEFAULT NULL,
    KEY idx_outbox_pending (entity_type, status, created_at)
) COMMENT='ES 同步 Outbox';

-- ============================================================
-- 5. data_task_rel 数据 ↔ 流水线任务关联（任务完成度统计）
-- ============================================================

CREATE TABLE data_task_rel (
    id              BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    entity_type     VARCHAR(16) NOT NULL COMMENT 'raw_data / asset_data',
    entity_id       BIGINT NOT NULL COMMENT 'raw_data.id 或 asset_data.id',
    storage_path    VARCHAR(1024) NOT NULL COMMENT '冗余路径，便于统计与看板展示',
    task_code       VARCHAR(32) NOT NULL COMMENT 'detect/clean/preprocess/audit/synthesize/tag',
    status          VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT 'pending/running/success/failed/skipped',
    sort_order      SMALLINT NOT NULL DEFAULT 0 COMMENT '流水线顺序',
    started_at      DATETIME DEFAULT NULL COMMENT '最近一次开始',
    finished_at     DATETIME DEFAULT NULL COMMENT '最近一次完成',
    duration_ms     BIGINT NOT NULL DEFAULT 0,
    job_id          BIGINT DEFAULT NULL COMMENT '批任务ID',
    attempt_count   INT NOT NULL DEFAULT 0 COMMENT '累计执行次数',
    error_message   TEXT,
    output_json     JSON DEFAULT NULL COMMENT '任务输出摘要',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_entity_task (entity_type, entity_id, task_code),
    KEY idx_task_storage_path (storage_path),
    KEY idx_task_code_status (task_code, status),
    KEY idx_task_entity (entity_type, entity_id)
) COMMENT='数据任务关联：每条数据每个任务一行，记录最新完成状态';
