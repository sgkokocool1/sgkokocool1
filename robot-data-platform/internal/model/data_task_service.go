package model

import (
	"time"

	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

// InitDataTaskRels 数据入库时初始化任务关联行（全部 pending）
func InitDataTaskRels(db *gorm.DB, entityType DataEntityType, entityID uint64, storagePath string) error {
	tasks := pipelineTasks(entityType)
	rels := make([]DataTaskRel, 0, len(tasks))
	for i, code := range tasks {
		rels = append(rels, DataTaskRel{
			EntityType:  entityType,
			EntityID:    entityID,
			StoragePath: storagePath,
			TaskCode:    code,
			Status:      TaskStatusPending,
			SortOrder:   int16(i + 1),
		})
	}
	return db.Clauses(clause.OnConflict{DoNothing: true}).Create(&rels).Error
}

// UpsertDataTaskRel 任务开始或完成时更新关联（每个任务每个数据仅保留最新状态）
func UpsertDataTaskRel(db *gorm.DB, in CompleteTaskInput) error {
	now := time.Now()
	finishedAt := in.FinishedAt
	if finishedAt == nil && (in.Status == TaskStatusSuccess || in.Status == TaskStatusFailed || in.Status == TaskStatusSkipped) {
		finishedAt = &now
	}
	sortOrder := taskSortOrder(in.EntityType, in.TaskCode)

	row := DataTaskRel{
		EntityType:   in.EntityType,
		EntityID:     in.EntityID,
		StoragePath:  in.StoragePath,
		TaskCode:     in.TaskCode,
		Status:       in.Status,
		SortOrder:    sortOrder,
		StartedAt:    in.StartedAt,
		FinishedAt:   finishedAt,
		DurationMs:   in.DurationMs,
		JobID:        in.JobID,
		ErrorMessage: in.ErrorMessage,
		OutputJSON:   in.OutputJSON,
	}
	if in.Status == TaskStatusRunning || in.Status == TaskStatusSuccess || in.Status == TaskStatusFailed {
		row.AttemptCount = 1
	}

	return db.Clauses(clause.OnConflict{
		Columns: []clause.Column{
			{Name: "entity_type"},
			{Name: "entity_id"},
			{Name: "task_code"},
		},
		DoUpdates: clause.Assignments(map[string]interface{}{
			"storage_path":  in.StoragePath,
			"status":        in.Status,
			"sort_order":    sortOrder,
			"started_at":    gorm.Expr("COALESCE(VALUES(started_at), started_at)"),
			"finished_at":   finishedAt,
			"duration_ms":   in.DurationMs,
			"job_id":        in.JobID,
			"error_message": in.ErrorMessage,
			"output_json":   in.OutputJSON,
			"attempt_count": gorm.Expr("attempt_count + ?", bumpAttempt(in.Status)),
			"updated_at":    now,
		}),
	}).Create(&row).Error
}

// GetDataTaskProgress 统计单条数据的任务完成情况
func GetDataTaskProgress(db *gorm.DB, entityType DataEntityType, entityID uint64) (*DataTaskProgress, error) {
	var rels []DataTaskRel
	if err := db.Where("entity_type = ? AND entity_id = ?", entityType, entityID).
		Order("sort_order ASC").Find(&rels).Error; err != nil {
		return nil, err
	}
	if len(rels) == 0 {
		return &DataTaskProgress{EntityType: entityType, EntityID: entityID}, nil
	}

	p := &DataTaskProgress{
		EntityType:  entityType,
		EntityID:    entityID,
		StoragePath: rels[0].StoragePath,
		TotalTasks:  int32(len(rels)),
	}
	for _, r := range rels {
		switch r.Status {
		case TaskStatusSuccess, TaskStatusSkipped:
			p.CompletedTasks++
		case TaskStatusFailed:
			p.FailedTasks++
		case TaskStatusRunning:
			p.RunningTasks++
		default:
			p.PendingTasks++
		}
	}
	if p.TotalTasks > 0 {
		p.ProgressPct = float64(p.CompletedTasks) * 100 / float64(p.TotalTasks)
	}
	p.IsAllDone = p.CompletedTasks == p.TotalTasks
	return p, nil
}

// ListDataTaskRels 查询某条数据全部任务关联
func ListDataTaskRels(db *gorm.DB, entityType DataEntityType, entityID uint64) ([]DataTaskRel, error) {
	var rels []DataTaskRel
	err := db.Where("entity_type = ? AND entity_id = ?", entityType, entityID).
		Order("sort_order ASC").Find(&rels).Error
	return rels, err
}

func pipelineTasks(entityType DataEntityType) []ProcessingStage {
	if entityType == EntityAssetData {
		return AssetDataPipelineTasks
	}
	return RawDataPipelineTasks
}

func taskSortOrder(entityType DataEntityType, code ProcessingStage) int16 {
	for i, t := range pipelineTasks(entityType) {
		if t == code {
			return int16(i + 1)
		}
	}
	return 0
}

func bumpAttempt(status DataTaskStatus) int32 {
	if status == TaskStatusRunning {
		return 1
	}
	return 0
}
