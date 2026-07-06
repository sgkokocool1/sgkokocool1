package model

import (
	"time"

	"gorm.io/datatypes"
)

// DataTaskRel 数据 ↔ 流水线任务 关联表（每条数据每个任务一行，记录最新完成状态）
// 任务完成时 UPSERT 本表；processing_log 保留每次执行明细
type DataTaskRel struct {
	ID           uint64          `gorm:"primaryKey;autoIncrement"`
	EntityType   DataEntityType  `gorm:"type:varchar(16);not null;uniqueIndex:uk_entity_task,priority:1;index:idx_task_entity,priority:1;comment:raw_data/asset_data"`
	EntityID     uint64          `gorm:"not null;uniqueIndex:uk_entity_task,priority:2;index:idx_task_entity,priority:2"`
	StoragePath  string          `gorm:"type:varchar(1024);not null;index;comment:冗余路径，便于统计展示"`
	TaskCode     ProcessingStage `gorm:"type:varchar(32);not null;uniqueIndex:uk_entity_task,priority:3;index:idx_task_code_status,priority:1;comment:detect/clean/preprocess/audit/synthesize/tag"`
	Status       DataTaskStatus  `gorm:"type:varchar(16);not null;default:pending;index:idx_task_code_status,priority:2"`
	SortOrder    int16           `gorm:"not null;default:0;comment:流水线顺序，用于完成度计算"`
	StartedAt    *time.Time      `gorm:"comment:最近一次开始时间"`
	FinishedAt   *time.Time      `gorm:"index;comment:最近一次完成时间"`
	DurationMs   int64           `gorm:"default:0"`
	JobID        *uint64         `gorm:"index;comment:批任务ID"`
	AttemptCount int32           `gorm:"default:0;comment:累计执行次数"`
	ErrorMessage string          `gorm:"type:text"`
	OutputJSON   datatypes.JSON  `gorm:"type:jsonb;comment:任务输出摘要"`
	CreatedAt    time.Time       `gorm:"autoCreateTime"`
	UpdatedAt    time.Time       `gorm:"autoUpdateTime"`
}

func (DataTaskRel) TableName() string { return "data_task_rel" }

// DataTaskProgress 单条数据的任务完成度（统计查询结果）
type DataTaskProgress struct {
	EntityType    DataEntityType `json:"entity_type"`
	EntityID      uint64         `json:"entity_id"`
	StoragePath   string         `json:"storage_path"`
	TotalTasks    int32          `json:"total_tasks"`
	CompletedTasks int32         `json:"completed_tasks"`
	FailedTasks   int32          `json:"failed_tasks"`
	RunningTasks  int32          `json:"running_tasks"`
	PendingTasks  int32          `json:"pending_tasks"`
	ProgressPct   float64        `json:"progress_pct"`
	IsAllDone     bool           `json:"is_all_done"`
}

// CompleteTaskInput 任务完成时写入关联表
type CompleteTaskInput struct {
	EntityType   DataEntityType
	EntityID     uint64
	StoragePath  string
	TaskCode     ProcessingStage
	Status       DataTaskStatus
	StartedAt    *time.Time
	FinishedAt   *time.Time
	DurationMs   int64
	JobID        *uint64
	ErrorMessage string
	OutputJSON   datatypes.JSON
}
