package model

// RawDataSourceType 原始数据来源（对应图中：采集数据 / 开源数据）
type RawDataSourceType string

const (
	RawSourceCollected   RawDataSourceType = "collected"    // 采集数据
	RawSourceOpenSource  RawDataSourceType = "open_source"  // 开源数据
	RawSourceSimulation  RawDataSourceType = "simulation"   // 仿真生成（扩展）
	RawSourceImported    RawDataSourceType = "imported"     // 外部导入
)

// RawDataType 原始数据类型（物理格式 / 模态）
type RawDataType string

const (
	RawTypeRosBag       RawDataType = "ros_bag"        // ROS1 bag
	RawTypeRosMCAP      RawDataType = "ros_mcap"       // ROS2 mcap
	RawTypeMP4          RawDataType = "mp4"            // 纯视频
	RawTypeHDF5         RawDataType = "hdf5"           // 仿真 rollout
	RawTypeParquet      RawDataType = "parquet"        // 已导出表格
	RawTypeEpisodeDir   RawDataType = "episode_dir"    // 目录型 episode（states+cameras）
	RawTypeMultiModal   RawDataType = "multi_modal"    // 混合目录
	RawTypeOther        RawDataType = "other"
)

// RawDataStatus 原始数据状态（对应图中状态机）
type RawDataStatus string

const (
	RawStatusInit       RawDataStatus = "init"       // 检测入库后 INIT
	RawStatusCorrect    RawDataStatus = "correct"    // 清洗通过：数据正确
	RawStatusAnomaly    RawDataStatus = "anomaly"    // 清洗失败：数据异常
	RawStatusProcessing RawDataStatus = "processing" // 打标预处理中
	RawStatusFinished   RawDataStatus = "finished"   // 预处理完成
	RawStatusArchived   RawDataStatus = "archived"   // 已归档（冷存储）
	RawStatusDeleted    RawDataStatus = "deleted"    // 逻辑删除标记（配合 soft delete）
)

// AssetDataType 资产数据类型
type AssetDataType string

const (
	AssetTypeLeRobotDataset AssetDataType = "lerobot_dataset" // LeRobot v3 数据集
	AssetTypeTrainingPack   AssetDataType = "training_pack"   // 训练用子集
	AssetTypeEvalPack       AssetDataType = "eval_pack"       // 评测集
	AssetTypeSynthetic      AssetDataType = "synthetic"       // 合成数据资产
	AssetTypeFeatureStore   AssetDataType = "feature_store" // 特征库（扩展）
)

// AssetDataStatus 资产数据状态
type AssetDataStatus string

const (
	AssetStatusInit       AssetDataStatus = "init"       // 审核入库 INIT
	AssetStatusAuditing   AssetDataStatus = "auditing"   // 审核中
	AssetStatusProcessing AssetDataStatus = "processing" // 合成中
	AssetStatusSuccess    AssetDataStatus = "success"    // 合成成功
	AssetStatusFailure    AssetDataStatus = "failure"    // 合成失败
	AssetStatusPublished  AssetDataStatus = "published"  // 已发布可用
	AssetStatusDeprecated AssetDataStatus = "deprecated" // 已废弃
)

// TagDomain 标签域：原始数据场景标签 vs 资产数据标签
type TagDomain string

const (
	TagDomainRaw   TagDomain = "raw"   // 场景标签（预处理阶段）
	TagDomainAsset TagDomain = "asset" // 资产标签（合成后）
)

// TagBindSource 标签绑定来源
type TagBindSource string

const (
	TagBindAuto   TagBindSource = "auto"
	TagBindManual TagBindSource = "manual"
	TagBindRule   TagBindSource = "rule"
)

// ProcessingStage 流水线阶段（与图中任务对应，用于审计日志）
type ProcessingStage string

const (
	StageDetect       ProcessingStage = "detect"        // 检测程序
	StageClean        ProcessingStage = "clean"         // 数据清洗
	StagePreprocess   ProcessingStage = "preprocess"    // 打标预处理
	StageAudit        ProcessingStage = "audit"         // 数据审核
	StageSynthesize   ProcessingStage = "synthesize"    // 数据合成
	StageTag          ProcessingStage = "tag"           // 数据标签
)
