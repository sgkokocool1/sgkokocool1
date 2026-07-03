package esdoc

import (
	"github.com/sgkokocool1/sgkokocool1/robot-data-platform/internal/model"
)

// BuildRawDataRecord 从 PG 模型构建 ES 文档（写入前调用）
func BuildRawDataRecord(raw model.RawData, tags []model.TagNode, _ map[uint64]model.RawDataTag) RawDataRecord {
	doc := RawDataRecord{
		RawDataID:      raw.ID,
		UUID:           raw.UUID,
		Code:           raw.Code,
		DataType:       string(raw.DataType),
		SourceType:     string(raw.SourceType),
		Status:         string(raw.Status),
		Name:           raw.Name,
		Description:    raw.Description,
		TaskName:       raw.TaskName,
		SceneCode:      raw.SceneCode,
		RobotID:        raw.RobotID,
		OperatorID:     raw.OperatorID,
		SessionKey:     raw.SessionKey,
		EpisodeName:    raw.EpisodeName,
		StoragePath:    raw.StoragePath,
		MetadataURI:    raw.MetadataURI,
		ManifestRef:    raw.ManifestRef,
		Checksum:       raw.Checksum,
		FileCount:      raw.FileCount,
		TotalBytes:     raw.TotalBytes,
		TotalFrames:    raw.TotalFrames,
		DurationSec:    raw.DurationSec,
		FPS:            raw.FPS,
		SuccessFlag:    raw.SuccessFlag,
		CollectedAt:    raw.CollectedAt,
		DetectedAt:     raw.DetectedAt,
		CleanedAt:      raw.CleanedAt,
		PreprocessedAt: raw.PreprocessedAt,
		CreatedAt:      raw.CreatedAt,
		UpdatedAt:      raw.UpdatedAt,
		SyncVersion:    raw.ESSyncVersion,
	}

	for _, t := range tags {
		doc.TagPaths = appendUniquePath(doc.TagPaths, model.NormalizeTagPath(t.Path))
	}
	return doc
}

// BuildAssetDataRecord 构建资产 ES 文档
func BuildAssetDataRecord(
	asset model.AssetData,
	tags []model.TagNode,
	_ map[uint64]model.AssetDataTag,
	sourceRawIDs []uint64,
	sourceRawUUIDs []string,
) AssetDataRecord {
	doc := AssetDataRecord{
		AssetDataID:        asset.ID,
		UUID:               asset.UUID,
		Code:               asset.Code,
		AssetType:          string(asset.AssetType),
		Status:             string(asset.Status),
		Name:               asset.Name,
		Description:        asset.Description,
		DatasetID:          asset.DatasetID,
		RobotType:          asset.RobotType,
		StoragePath:        asset.StoragePath,
		MetadataURI:        asset.MetadataURI,
		OutputURI:          asset.OutputURI,
		Checksum:           asset.Checksum,
		EpisodeCount:       asset.EpisodeCount,
		FrameCount:         asset.FrameCount,
		TaskCount:          asset.TaskCount,
		TotalBytes:         asset.TotalBytes,
		FPS:                asset.FPS,
		SourceRawDataIDs:   sourceRawIDs,
		SourceRawDataUUIDs: sourceRawUUIDs,
		AuditorID:          asset.AuditorID,
		AuditScore:         asset.AuditScore,
		ParentAssetID:      asset.ParentAssetID,
		AuditedAt:          asset.AuditedAt,
		SynthesizedAt:      asset.SynthesizedAt,
		PublishedAt:        asset.PublishedAt,
		CreatedAt:          asset.CreatedAt,
		UpdatedAt:          asset.UpdatedAt,
		SyncVersion:        asset.ESSyncVersion,
	}

	for _, t := range tags {
		doc.TagPaths = appendUniquePath(doc.TagPaths, model.NormalizeTagPath(t.Path))
	}
	return doc
}

func appendUniquePath(paths []string, path string) []string {
	if path == "" {
		return paths
	}
	for _, p := range paths {
		if p == path {
			return paths
		}
	}
	return append(paths, path)
}
