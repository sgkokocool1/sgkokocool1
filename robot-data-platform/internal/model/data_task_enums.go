package model

// DataEntityType 数据实体类型（任务关联主体）
type DataEntityType string

const (
	EntityRawData   DataEntityType = "raw_data"
	EntityAssetData DataEntityType = "asset_data"
)

// DataTaskStatus 单条数据上某任务的完成状态
type DataTaskStatus string

const (
	TaskStatusPending DataTaskStatus = "pending"
	TaskStatusRunning DataTaskStatus = "running"
	TaskStatusSuccess DataTaskStatus = "success"
	TaskStatusFailed  DataTaskStatus = "failed"
	TaskStatusSkipped DataTaskStatus = "skipped"
)

// RawDataPipelineTasks 原始数据流水线任务及顺序
var RawDataPipelineTasks = []ProcessingStage{
	StageDetect, StageClean, StagePreprocess, StageTag,
}

// AssetDataPipelineTasks 资产数据流水线任务及顺序
var AssetDataPipelineTasks = []ProcessingStage{
	StageAudit, StageSynthesize, StageTag,
}
