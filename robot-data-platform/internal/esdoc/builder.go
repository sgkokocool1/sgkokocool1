package esdoc

import (
	"strings"

	"github.com/sgkokocool1/sgkokocool1/robot-data-platform/internal/model"
)

// BuildRawDataRecord 从 PG 模型构建 ES 文档（写入前调用）
func BuildRawDataRecord(raw model.RawData, tags []model.TagNode, binds map[uint64]model.RawDataTag) RawDataRecord {
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

	var names []string
	for _, t := range tags {
		bind := binds[t.ID]
		doc.Tags = append(doc.Tags, TagRef{
			ID:         t.ID,
			Code:       t.Code,
			Name:       t.Name,
			Path:       t.Path,
			FullName:   t.FullName,
			Level:      t.Level,
			Domain:     string(t.Domain),
			Source:     string(bind.Source),
			Confidence: bind.Confidence,
		})
		doc.TagIDs = append(doc.TagIDs, t.ID)
		doc.TagPaths = appendAncestorPaths([]string{t.Path}, t.Path)
		doc.TagCodes = append(doc.TagCodes, t.Code)
		doc.TagNames = append(doc.TagNames, t.Name)
		names = append(names, t.Name)
	}
	doc.TagText = strings.Join(names, " ")
	return doc
}

// BuildAssetDataRecord 构建资产 ES 文档
func BuildAssetDataRecord(
	asset model.AssetData,
	tags []model.TagNode,
	binds map[uint64]model.AssetDataTag,
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
		CreatedAt:            asset.CreatedAt,
		UpdatedAt:            asset.UpdatedAt,
		SyncVersion:        asset.ESSyncVersion,
	}
	var names []string
	for _, t := range tags {
		bind := binds[t.ID]
		doc.Tags = append(doc.Tags, TagRef{
			ID: t.ID, Code: t.Code, Name: t.Name, Path: t.Path,
			FullName: t.FullName, Level: t.Level, Domain: string(t.Domain),
			Source: string(bind.Source), Confidence: bind.Confidence,
		})
		doc.TagIDs = append(doc.TagIDs, t.ID)
		doc.TagPaths = appendAncestorPaths([]string{t.Path}, t.Path)
		doc.TagCodes = append(doc.TagCodes, t.Code)
		doc.TagNames = append(doc.TagNames, t.Name)
		names = append(names, t.Name)
	}
	doc.TagText = strings.Join(names, " ")
	return doc
}

func appendAncestorPaths(paths []string, materialized string) []string {
	parts := strings.Split(strings.Trim(materialized, "/"), "/")
	for i := 1; i <= len(parts); i++ {
		p := "/" + strings.Join(parts[:i], "/")
		if !contains(paths, p) {
			paths = append(paths, p)
		}
	}
	return paths
}

func contains(ss []string, s string) bool {
	for _, v := range ss {
		if v == s {
			return true
		}
	}
	return false
}
