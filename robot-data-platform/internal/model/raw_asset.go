package model

import (
	"time"

	"gorm.io/datatypes"
	"gorm.io/gorm"
)

// RawData 原始数据表
// 对应流程图：采集/开源 → 检测入库(INIT) → 清洗(correct/anomaly) → 预处理(processing/finished)
type RawData struct {
	// --- 主键与对外标识 ---
	ID   uint64 `gorm:"primaryKey;autoIncrement;comment:内部主键"`
	UUID string `gorm:"type:char(36);uniqueIndex;not null;comment:对外唯一ID(UUID v4)"`

	// --- 分类（图中：数据类型） ---
	DataType   RawDataType       `gorm:"type:varchar(32);not null;index:idx_raw_type_status,priority:1;comment:数据物理类型 ros_bag/mp4/episode_dir 等"`
	SourceType RawDataSourceType `gorm:"type:varchar(32);not null;index;comment:来源 collected/open_source"`

	// --- 状态机（图中：INIT/正确/异常/处理中/完成） ---
	Status        RawDataStatus `gorm:"type:varchar(32);not null;index:idx_raw_type_status,priority:2;default:init;comment:当前状态"`
	StatusMessage string        `gorm:"type:varchar(512);comment:状态说明或失败摘要"`
	PrevStatus    RawDataStatus `gorm:"type:varchar(32);comment:上一状态，便于审计回滚"`

	// --- 基本信息 ---
	Name        string `gorm:"type:varchar(256);not null;index;comment:可读名称"`
	Code        string `gorm:"type:varchar(128);uniqueIndex;comment:业务编码，如 RAW-20250716-0007"`
	Description string `gorm:"type:text;comment:描述"`

	// --- 存储与元数据链接（核心） ---
	StoragePath  string `gorm:"type:varchar(1024);not null;index;comment:物理根路径 如 /data/raw/2025-07-16/.../episode_007"`
	MetadataURI  string `gorm:"type:varchar(1024);comment:元数据入口 如 episode_meta.json 的绝对路径"`
	ManifestRef  string `gorm:"type:varchar(512);index;comment:关联 manifest.jsonl 的 path 字段"`
	PreviewURI   string `gorm:"type:varchar(1024);comment:预览资源链接 首帧图/缩略图"`
	Checksum     string `gorm:"type:char(64);index;comment:内容校验 SHA256（目录可为 manifest 哈希）"`

	// --- 规模统计 ---
	FileCount   int32   `gorm:"default:0;comment:文件数量"`
	TotalBytes  int64   `gorm:"default:0;comment:占用字节"`
	TotalFrames int32   `gorm:"default:0;comment:帧数（若适用）"`
	DurationSec float64 `gorm:"default:0;comment:时长秒"`
	FPS         float32 `gorm:"default:0;comment:采样帧率"`

	// --- 业务维度 ---
	RobotID     string `gorm:"type:varchar(64);index:idx_raw_robot_scene,priority:1;comment:机器人ID"`
	OperatorID  string `gorm:"type:varchar(64);index;comment:采集操作员"`
	SceneCode   string `gorm:"type:varchar(128);index:idx_raw_robot_scene,priority:2;comment:场景编码"`
	TaskName    string `gorm:"type:varchar(256);index;comment:任务名 pick_red_block"`
	SessionKey  string `gorm:"type:varchar(128);index;comment:采集会话 am_real_001"`
	EpisodeName string `gorm:"type:varchar(64);comment:episode_007"`
	SuccessFlag *bool  `gorm:"comment:采集是否成功 nullable"`

	// --- 时间线（各阶段完成时间，便于看板统计） ---
	CollectedAt    *time.Time `gorm:"index;comment:采集开始时间"`
	CollectionEnd  *time.Time `gorm:"comment:采集结束时间"`
	DetectedAt     *time.Time `gorm:"comment:检测入库时间 → INIT"`
	CleanedAt      *time.Time `gorm:"comment:清洗完成时间"`
	PreprocessedAt *time.Time `gorm:"comment:预处理完成时间 → finished"`
	ArchivedAt     *time.Time `gorm:"comment:归档时间"`

	// --- 扩展元数据（JSON，避免频繁改表） ---
	ExtraMeta datatypes.JSON `gorm:"type:jsonb;comment:扩展字段 如 validation.json 摘要"`
	SchemaVer string         `gorm:"type:varchar(16);default:v1;comment:feature schema 版本"`

	// --- ES 同步控制 ---
	ESSyncVersion int64      `gorm:"default:0;comment:同步版本号 每次变更递增"`
	ESIndexedAt   *time.Time `gorm:"comment:最近写入 ES 时间"`
	ESDocID       string     `gorm:"type:varchar(64);index;comment:ES 文档 _id 默认等于 UUID"`

	// --- 版本与审计 ---
	Version   int32          `gorm:"default:1;comment:乐观锁"`
	CreatedBy string         `gorm:"type:varchar(64);comment:创建人/系统"`
	UpdatedBy string         `gorm:"type:varchar(64);comment:最后修改人"`
	CreatedAt time.Time      `gorm:"autoCreateTime"`
	UpdatedAt time.Time      `gorm:"autoUpdateTime"`
	DeletedAt gorm.DeletedAt `gorm:"index;comment:软删除"`

	// --- 关联 ---
	Tags         []RawDataTag         `gorm:"foreignKey:RawDataID"`
	ProcessLogs  []ProcessingLog      `gorm:"foreignKey:RawDataID"`
	AssetSources []AssetDataRawSource `gorm:"foreignKey:RawDataID"`
}

func (RawData) TableName() string { return "raw_data" }

// AssetData 资产数据表
// 对应流程图：审核入库(INIT) → 合成(success/failure) → 打标入 ES
type AssetData struct {
	ID   uint64 `gorm:"primaryKey;autoIncrement;comment:内部主键"`
	UUID string `gorm:"type:char(36);uniqueIndex;not null;comment:对外唯一ID"`

	// --- 分类 ---
	AssetType AssetDataType `gorm:"type:varchar(32);not null;index:idx_asset_type_status,priority:1;comment:资产类型 lerobot_dataset 等"`
	Status    AssetDataStatus `gorm:"type:varchar(32);not null;index:idx_asset_type_status,priority:2;default:init;comment:当前状态"`
	StatusMessage string      `gorm:"type:varchar(512);comment:状态说明"`
	PrevStatus    AssetDataStatus `gorm:"type:varchar(32);comment:上一状态"`

	// --- 基本信息 ---
	Name        string `gorm:"type:varchar(256);not null;index;comment:资产名称"`
	Code        string `gorm:"type:varchar(128);uniqueIndex;comment:业务编码 ASSET-pick-place-v1"`
	Description string `gorm:"type:text;comment:描述"`

	// --- 存储与链接 ---
	StoragePath string `gorm:"type:varchar(1024);not null;index;comment:资产根路径 /data/lerobot/..."`
	DatasetID   string `gorm:"type:varchar(256);index;comment:数据集标识 local/pick-place-v1"`
	MetadataURI string `gorm:"type:varchar(1024);comment:meta/info.json 路径"`
	OutputURI   string `gorm:"type:varchar(1024);comment:训练入口或发布地址"`
	Checksum    string `gorm:"type:char(64);comment:资产校验和"`

	// --- 规模 ---
	EpisodeCount int32 `gorm:"default:0;comment:episode 数"`
	FrameCount   int64 `gorm:"default:0;comment:总帧数"`
	TaskCount    int32 `gorm:"default:0;comment:任务种类数"`
	TotalBytes   int64 `gorm:"default:0;comment:占用字节"`
	FPS          float32 `gorm:"default:0;comment:帧率"`
	RobotType    string  `gorm:"type:varchar(64);index;comment:机器人类型"`

	// --- 合成与审核 ---
	SynthesisConfig datatypes.JSON `gorm:"type:jsonb;comment:合成参数 date_from/date_to/filter 等"`
	AuditResult     datatypes.JSON `gorm:"type:jsonb;comment:审核结果 auto/manual"`
	AuditorID       string         `gorm:"type:varchar(64);comment:审核人"`
	AuditScore      *float32       `gorm:"comment:审核评分 0-1"`
	ParentAssetID   *uint64        `gorm:"index;comment:父版本资产ID（增量构建）"`
	BuildJobID      *uint64        `gorm:"index;comment:关联 processing_jobs.id"`

	// --- 时间线 ---
	AuditedAt     *time.Time `gorm:"comment:审核完成"`
	SynthesizedAt *time.Time `gorm:"comment:合成完成"`
	PublishedAt   *time.Time `gorm:"comment:发布时间"`
	DeprecatedAt  *time.Time `gorm:"comment:废弃时间"`

	ExtraMeta datatypes.JSON `gorm:"type:jsonb;comment:扩展元数据"`

	// --- ES 同步 ---
	ESSyncVersion int64      `gorm:"default:0"`
	ESIndexedAt   *time.Time `gorm:"comment:最近 ES 同步时间"`
	ESDocID       string     `gorm:"type:varchar(64);index;comment:ES _id"`

	Version   int32          `gorm:"default:1"`
	CreatedBy string         `gorm:"type:varchar(64)"`
	UpdatedBy string         `gorm:"type:varchar(64)"`
	CreatedAt time.Time      `gorm:"autoCreateTime"`
	UpdatedAt time.Time      `gorm:"autoUpdateTime"`
	DeletedAt gorm.DeletedAt `gorm:"index"`

	// --- 关联：多原始数据合成一个资产 ---
	RawSources []AssetDataRawSource `gorm:"foreignKey:AssetDataID"`
	Tags       []AssetDataTag       `gorm:"foreignKey:AssetDataID"`
	ProcessLogs []ProcessingLog     `gorm:"foreignKey:AssetDataID"`
}

func (AssetData) TableName() string { return "asset_data" }

// AssetDataRawSource 资产 ← 原始数据 多对多关联表
// 一个 LeRobot 数据集可由多条 raw episode 合成
type AssetDataRawSource struct {
	ID          uint64 `gorm:"primaryKey;autoIncrement"`
	AssetDataID uint64 `gorm:"not null;uniqueIndex:uk_asset_raw,priority:1;index;comment:资产ID"`
	RawDataID   uint64 `gorm:"not null;uniqueIndex:uk_asset_raw,priority:2;index;comment:原始数据ID"`
	Role        string `gorm:"type:varchar(32);default:primary;comment:primary/supplement/filtered_out"`
	Weight      float32 `gorm:"default:1;comment:合成权重"`
	CreatedAt   time.Time `gorm:"autoCreateTime"`

	AssetData AssetData `gorm:"foreignKey:AssetDataID"`
	RawData   RawData   `gorm:"foreignKey:RawDataID"`
}

func (AssetDataRawSource) TableName() string { return "asset_data_raw_source" }

// ProcessingLog 流水线阶段日志（对应图中各阶段任务）
type ProcessingLog struct {
	ID          uint64          `gorm:"primaryKey;autoIncrement"`
	RawDataID   *uint64         `gorm:"index;comment:原始数据ID 可空"`
	AssetDataID *uint64         `gorm:"index;comment:资产数据ID 可空"`
	Stage       ProcessingStage `gorm:"type:varchar(32);not null;index;comment:detect/clean/preprocess/audit/synthesize/tag"`
	JobID       *uint64         `gorm:"index;comment:批任务ID"`
	Status      string          `gorm:"type:varchar(32);not null;comment:running/success/failed"`
	InputJSON   datatypes.JSON  `gorm:"type:jsonb"`
	OutputJSON  datatypes.JSON  `gorm:"type:jsonb"`
	ErrorMsg    string          `gorm:"type:text"`
	StartedAt   time.Time       `gorm:"not null;index"`
	FinishedAt  *time.Time      `gorm:"index"`
	DurationMs  int64           `gorm:"default:0"`
	OperatorID  string          `gorm:"type:varchar(64)"`
	CreatedAt   time.Time       `gorm:"autoCreateTime"`
}

func (ProcessingLog) TableName() string { return "processing_log" }
