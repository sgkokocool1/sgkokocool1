package esdoc

import "time"

// TagRef ES 内嵌标签（冗余树信息，避免查询时再 join PG）
type TagRef struct {
	ID       uint64  `json:"id"`
	Code     string  `json:"code"`
	Name     string  `json:"name"`
	Path     string  `json:"path"`      // /scene/indoor/kitchen
	FullName string  `json:"full_name"` // 场景/室内/厨房
	Level    int16   `json:"level"`
	Domain   string  `json:"domain"` // raw | asset
	Source   string  `json:"source"` // auto | manual | rule
	Confidence float32 `json:"confidence,omitempty"`
}

// RawDataRecord 原始数据 ES 文档（索引：raw_data_records）
// _id 建议使用 UUID，与 PG raw_data.uuid 一致
type RawDataRecord struct {
	// 标识
	RawDataID uint64 `json:"raw_data_id"`
	UUID      string `json:"uuid"`
	Code      string `json:"code"`

	// 分类与状态
	DataType   string `json:"data_type"`
	SourceType string `json:"source_type"`
	Status     string `json:"status"`

	// 可检索文本
	Name        string `json:"name"`
	Description string `json:"description"`
	TaskName    string `json:"task_name"`
	SceneCode   string `json:"scene_code"`
	RobotID     string `json:"robot_id"`
	OperatorID  string `json:"operator_id"`
	SessionKey  string `json:"session_key"`
	EpisodeName string `json:"episode_name"`

	// 存储链接（通常不作为全文检索，keyword 过滤）
	StoragePath string `json:"storage_path"`
	MetadataURI string `json:"metadata_uri"`
	ManifestRef string `json:"manifest_ref"`
	Checksum    string `json:"checksum"`

	// 统计
	FileCount   int32   `json:"file_count"`
	TotalBytes  int64   `json:"total_bytes"`
	TotalFrames int32   `json:"total_frames"`
	DurationSec float64 `json:"duration_sec"`
	FPS         float32 `json:"fps"`
	SuccessFlag *bool   `json:"success_flag,omitempty"`

	// --- 树状标签（检索核心） ---
	Tags []TagRef `json:"tags"` // nested 存储

	// 扁平化字段（高性能过滤，避免 nested 聚合开销）
	TagIDs    []uint64 `json:"tag_ids"`    // terms 精确匹配
	TagPaths  []string `json:"tag_paths"`  // prefix 子树检索 key
	TagCodes  []string `json:"tag_codes"`  // keyword
	TagNames  []string `json:"tag_names"`  // 中文名 terms
	TagText   string   `json:"tag_text"`   // 所有标签名拼接，match 模糊搜

	// 时间
	CollectedAt    *time.Time `json:"collected_at,omitempty"`
	DetectedAt     *time.Time `json:"detected_at,omitempty"`
	CleanedAt      *time.Time `json:"cleaned_at,omitempty"`
	PreprocessedAt *time.Time `json:"preprocessed_at,omitempty"`
	CreatedAt      time.Time  `json:"created_at"`
	UpdatedAt      time.Time  `json:"updated_at"`

	// 同步
	SyncVersion int64 `json:"sync_version"`
}

// AssetDataRecord 资产数据 ES 文档（索引：asset_data_records）
type AssetDataRecord struct {
	AssetDataID uint64 `json:"asset_data_id"`
	UUID        string `json:"uuid"`
	Code        string `json:"code"`

	AssetType string `json:"asset_type"`
	Status    string `json:"status"`

	Name        string `json:"name"`
	Description string `json:"description"`
	DatasetID   string `json:"dataset_id"`
	RobotType   string `json:"robot_type"`

	StoragePath string `json:"storage_path"`
	MetadataURI string `json:"metadata_uri"`
	OutputURI   string `json:"output_uri"`
	Checksum    string `json:"checksum"`

	EpisodeCount int32 `json:"episode_count"`
	FrameCount   int64 `json:"frame_count"`
	TaskCount    int32 `json:"task_count"`
	TotalBytes   int64 `json:"total_bytes"`
	FPS          float32 `json:"fps"`

	// 来源原始数据 ID 列表（检索「某批 raw 生成了哪些资产」）
	SourceRawDataIDs   []uint64 `json:"source_raw_data_ids"`
	SourceRawDataUUIDs []string `json:"source_raw_data_uuids"`

	Tags     []TagRef `json:"tags"`
	TagIDs   []uint64 `json:"tag_ids"`
	TagPaths []string `json:"tag_paths"`
	TagCodes []string `json:"tag_codes"`
	TagNames []string `json:"tag_names"`
	TagText  string   `json:"tag_text"`

	AuditorID     string     `json:"auditor_id,omitempty"`
	AuditScore    *float32   `json:"audit_score,omitempty"`
	ParentAssetID *uint64    `json:"parent_asset_id,omitempty"`
	AuditedAt     *time.Time `json:"audited_at,omitempty"`
	SynthesizedAt *time.Time `json:"synthesized_at,omitempty"`
	PublishedAt   *time.Time `json:"published_at,omitempty"`
	CreatedAt     time.Time  `json:"created_at"`
	UpdatedAt     time.Time  `json:"updated_at"`

	SyncVersion int64 `json:"sync_version"`
}
