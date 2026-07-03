-- 机器人数据平台 · PostgreSQL DDL
-- 设计文档：docs/robot-data-platform/DESIGN.md

-- ============================================================
-- 枚举类型（也可用 varchar + 应用层校验）
-- ============================================================

CREATE TYPE raw_data_source_type AS ENUM ('collected', 'open_source', 'simulation', 'imported');
CREATE TYPE raw_data_type AS ENUM (
    'ros_bag', 'ros_mcap', 'mp4', 'hdf5', 'parquet',
    'episode_dir', 'multi_modal', 'other'
);
CREATE TYPE raw_data_status AS ENUM (
    'init', 'correct', 'anomaly', 'processing', 'finished', 'archived', 'deleted'
);
CREATE TYPE asset_data_type AS ENUM (
    'lerobot_dataset', 'training_pack', 'eval_pack', 'synthetic', 'feature_store'
);
CREATE TYPE asset_data_status AS ENUM (
    'init', 'auditing', 'processing', 'success', 'failure', 'published', 'deprecated'
);
CREATE TYPE tag_domain AS ENUM ('raw', 'asset');
CREATE TYPE tag_bind_source AS ENUM ('auto', 'manual', 'rule');
CREATE TYPE processing_stage AS ENUM (
    'detect', 'clean', 'preprocess', 'audit', 'synthesize', 'tag'
);

-- ============================================================
-- 1. raw_data 原始数据
-- ============================================================

CREATE TABLE raw_data (
    id                  BIGSERIAL PRIMARY KEY,
    uuid                CHAR(36) NOT NULL UNIQUE,
    data_type           raw_data_type NOT NULL,
    source_type         raw_data_source_type NOT NULL,
    status              raw_data_status NOT NULL DEFAULT 'init',
    status_message      VARCHAR(512),
    prev_status         raw_data_status,
    name                VARCHAR(256) NOT NULL,
    code                VARCHAR(128) UNIQUE,
    description         TEXT,
    storage_path        VARCHAR(1024) NOT NULL,
    metadata_uri        VARCHAR(1024),
    manifest_ref        VARCHAR(512),
    preview_uri         VARCHAR(1024),
    checksum            CHAR(64),
    file_count          INTEGER NOT NULL DEFAULT 0,
    total_bytes         BIGINT NOT NULL DEFAULT 0,
    total_frames        INTEGER NOT NULL DEFAULT 0,
    duration_sec        DOUBLE PRECISION NOT NULL DEFAULT 0,
    fps                 REAL NOT NULL DEFAULT 0,
    robot_id            VARCHAR(64),
    operator_id         VARCHAR(64),
    scene_code          VARCHAR(128),
    task_name           VARCHAR(256),
    session_key         VARCHAR(128),
    episode_name        VARCHAR(64),
    success_flag        BOOLEAN,
    collected_at        TIMESTAMPTZ,
    collection_end      TIMESTAMPTZ,
    detected_at         TIMESTAMPTZ,
    cleaned_at          TIMESTAMPTZ,
    preprocessed_at     TIMESTAMPTZ,
    archived_at         TIMESTAMPTZ,
    extra_meta          JSONB,
    schema_ver          VARCHAR(16) NOT NULL DEFAULT 'v1',
    es_sync_version     BIGINT NOT NULL DEFAULT 0,
    es_indexed_at       TIMESTAMPTZ,
    es_doc_id           VARCHAR(64),
    version             INTEGER NOT NULL DEFAULT 1,
    created_by          VARCHAR(64),
    updated_by          VARCHAR(64),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_raw_type_status ON raw_data (data_type, status);
CREATE INDEX idx_raw_robot_scene ON raw_data (robot_id, scene_code);
CREATE INDEX idx_raw_manifest_ref ON raw_data (manifest_ref);
CREATE INDEX idx_raw_collected_at ON raw_data (collected_at);
CREATE INDEX idx_raw_deleted_at ON raw_data (deleted_at);

-- ============================================================
-- 2. asset_data 资产数据
-- ============================================================

CREATE TABLE asset_data (
    id                  BIGSERIAL PRIMARY KEY,
    uuid                CHAR(36) NOT NULL UNIQUE,
    asset_type          asset_data_type NOT NULL,
    status              asset_data_status NOT NULL DEFAULT 'init',
    status_message      VARCHAR(512),
    prev_status         asset_data_status,
    name                VARCHAR(256) NOT NULL,
    code                VARCHAR(128) UNIQUE,
    description         TEXT,
    storage_path        VARCHAR(1024) NOT NULL,
    dataset_id          VARCHAR(256),
    metadata_uri        VARCHAR(1024),
    output_uri          VARCHAR(1024),
    checksum            CHAR(64),
    episode_count       INTEGER NOT NULL DEFAULT 0,
    frame_count         BIGINT NOT NULL DEFAULT 0,
    task_count          INTEGER NOT NULL DEFAULT 0,
    total_bytes         BIGINT NOT NULL DEFAULT 0,
    fps                 REAL NOT NULL DEFAULT 0,
    robot_type          VARCHAR(64),
    synthesis_config    JSONB,
    audit_result        JSONB,
    auditor_id          VARCHAR(64),
    audit_score         REAL,
    parent_asset_id     BIGINT REFERENCES asset_data(id),
    build_job_id        BIGINT,
    audited_at          TIMESTAMPTZ,
    synthesized_at      TIMESTAMPTZ,
    published_at        TIMESTAMPTZ,
    deprecated_at       TIMESTAMPTZ,
    extra_meta          JSONB,
    es_sync_version     BIGINT NOT NULL DEFAULT 0,
    es_indexed_at       TIMESTAMPTZ,
    es_doc_id           VARCHAR(64),
    version             INTEGER NOT NULL DEFAULT 1,
    created_by          VARCHAR(64),
    updated_by          VARCHAR(64),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_asset_type_status ON asset_data (asset_type, status);
CREATE INDEX idx_asset_dataset_id ON asset_data (dataset_id);
CREATE INDEX idx_asset_parent ON asset_data (parent_asset_id);
CREATE INDEX idx_asset_deleted_at ON asset_data (deleted_at);

-- ============================================================
-- 3. asset_data_raw_source 资产 ← 原始数据 多对多
-- ============================================================

CREATE TABLE asset_data_raw_source (
    id              BIGSERIAL PRIMARY KEY,
    asset_data_id   BIGINT NOT NULL REFERENCES asset_data(id) ON DELETE CASCADE,
    raw_data_id     BIGINT NOT NULL REFERENCES raw_data(id) ON DELETE RESTRICT,
    role            VARCHAR(32) NOT NULL DEFAULT 'primary',
    weight          REAL NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (asset_data_id, raw_data_id)
);

CREATE INDEX idx_asset_raw_raw_id ON asset_data_raw_source (raw_data_id);

-- ============================================================
-- 4. tag_node 标签树
-- ============================================================

CREATE TABLE tag_node (
    id          BIGSERIAL PRIMARY KEY,
    parent_id   BIGINT REFERENCES tag_node(id),
    domain      tag_domain NOT NULL,
    category    VARCHAR(64) NOT NULL,
    path        VARCHAR(1024) NOT NULL,
    name        VARCHAR(256) NOT NULL,
    is_leaf     BOOLEAN NOT NULL DEFAULT FALSE,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    UNIQUE (domain, path)
);

CREATE INDEX idx_tag_parent ON tag_node (parent_id);
CREATE INDEX idx_tag_category ON tag_node (domain, category);
CREATE INDEX idx_tag_leaf ON tag_node (is_leaf) WHERE is_leaf = TRUE;

-- ============================================================
-- 5. raw_data_tag / asset_data_tag 标签绑定
-- ============================================================

CREATE TABLE raw_data_tag (
    id          BIGSERIAL PRIMARY KEY,
    raw_data_id BIGINT NOT NULL REFERENCES raw_data(id) ON DELETE CASCADE,
    tag_id      BIGINT NOT NULL REFERENCES tag_node(id) ON DELETE RESTRICT,
    source      tag_bind_source NOT NULL DEFAULT 'auto',
    confidence  REAL NOT NULL DEFAULT 1,
    bound_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bound_by    VARCHAR(64),
    UNIQUE (raw_data_id, tag_id)
);

CREATE INDEX idx_raw_tag_tag_id ON raw_data_tag (tag_id);

CREATE TABLE asset_data_tag (
    id              BIGSERIAL PRIMARY KEY,
    asset_data_id   BIGINT NOT NULL REFERENCES asset_data(id) ON DELETE CASCADE,
    tag_id          BIGINT NOT NULL REFERENCES tag_node(id) ON DELETE RESTRICT,
    source          tag_bind_source NOT NULL DEFAULT 'manual',
    confidence      REAL NOT NULL DEFAULT 1,
    bound_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bound_by        VARCHAR(64),
    UNIQUE (asset_data_id, tag_id)
);

CREATE INDEX idx_asset_tag_tag_id ON asset_data_tag (tag_id);

-- ============================================================
-- 6. processing_log 流水线阶段日志
-- ============================================================

CREATE TABLE processing_log (
    id              BIGSERIAL PRIMARY KEY,
    raw_data_id     BIGINT REFERENCES raw_data(id) ON DELETE SET NULL,
    asset_data_id   BIGINT REFERENCES asset_data(id) ON DELETE SET NULL,
    stage           processing_stage NOT NULL,
    job_id          BIGINT,
    status          VARCHAR(32) NOT NULL,
    input_json      JSONB,
    output_json     JSONB,
    error_msg       TEXT,
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ,
    duration_ms     BIGINT NOT NULL DEFAULT 0,
    operator_id     VARCHAR(64),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_plog_raw ON processing_log (raw_data_id);
CREATE INDEX idx_plog_asset ON processing_log (asset_data_id);
CREATE INDEX idx_plog_stage ON processing_log (stage, status);
CREATE INDEX idx_plog_started ON processing_log (started_at);

-- ============================================================
-- 7. es_sync_outbox ES 同步 Outbox
-- ============================================================

CREATE TABLE es_sync_outbox (
    id              BIGSERIAL PRIMARY KEY,
    entity_type     VARCHAR(32) NOT NULL,
    entity_id       BIGINT NOT NULL,
    entity_uuid     CHAR(36) NOT NULL,
    op              VARCHAR(16) NOT NULL,
    payload         JSONB NOT NULL,
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    retry_count     INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ
);

CREATE INDEX idx_outbox_pending ON es_sync_outbox (entity_type, status, created_at);
