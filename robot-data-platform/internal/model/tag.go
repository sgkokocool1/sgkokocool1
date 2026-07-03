package model

import (
	"strings"
	"time"

	"gorm.io/gorm"
)

// TagNode 树状标签节点（PG 存权威树结构，ES 仅冗余 path）
type TagNode struct {
	ID       uint64    `gorm:"primaryKey;autoIncrement"`
	ParentID *uint64   `gorm:"index;comment:父节点ID NULL 表示根"`
	Domain   TagDomain `gorm:"type:varchar(16);not null;uniqueIndex:uk_tag_domain_path,priority:1;index;comment:raw 场景标签 / asset 资产标签"`

	// Category 大类，与 path 第一段一致，如 scene / task / quality
	Category string `gorm:"type:varchar(64);not null;index;comment:大类 对应 path 首段"`
	// Path 物化路径，无 leading slash，如 scene/indoor/kitchen
	Path string `gorm:"type:varchar(1024);not null;uniqueIndex:uk_tag_domain_path,priority:2;comment:物化路径 scene/indoor/kitchen"`
	Name string `gorm:"type:varchar(256);not null;comment:显示名 厨房"`

	IsLeaf   bool `gorm:"default:false;index;comment:是否叶子（可绑定）"`
	IsActive bool `gorm:"default:true;index;comment:是否启用"`

	CreatedAt time.Time      `gorm:"autoCreateTime"`
	UpdatedAt time.Time      `gorm:"autoUpdateTime"`
	DeletedAt gorm.DeletedAt `gorm:"index"`

	Parent   *TagNode  `gorm:"foreignKey:ParentID"`
	Children []TagNode `gorm:"foreignKey:ParentID"`
}

func (TagNode) TableName() string { return "tag_node" }

// NormalizeTagPath 统一 path 格式：去首尾斜杠
func NormalizeTagPath(path string) string {
	return strings.Trim(path, "/")
}

// TagCategoryFromPath 从 path 提取大类（第一段）
func TagCategoryFromPath(path string) string {
	path = NormalizeTagPath(path)
	if path == "" {
		return ""
	}
	if i := strings.Index(path, "/"); i >= 0 {
		return path[:i]
	}
	return path
}

// RawDataTag 原始数据 ↔ 标签 多对多
type RawDataTag struct {
	ID         uint64        `gorm:"primaryKey;autoIncrement"`
	RawDataID  uint64        `gorm:"not null;uniqueIndex:uk_raw_tag,priority:1;index"`
	TagID      uint64        `gorm:"not null;uniqueIndex:uk_raw_tag,priority:2;index"`
	Source     TagBindSource `gorm:"type:varchar(16);not null;default:auto;comment:auto/manual/rule"`
	Confidence float32       `gorm:"default:1;comment:自动打标置信度 0-1"`
	BoundAt    time.Time     `gorm:"autoCreateTime"`
	BoundBy    string        `gorm:"type:varchar(64)"`

	RawData RawData `gorm:"foreignKey:RawDataID"`
	Tag     TagNode `gorm:"foreignKey:TagID"`
}

func (RawDataTag) TableName() string { return "raw_data_tag" }

// AssetDataTag 资产数据 ↔ 标签 多对多
type AssetDataTag struct {
	ID          uint64        `gorm:"primaryKey;autoIncrement"`
	AssetDataID uint64        `gorm:"not null;uniqueIndex:uk_asset_tag,priority:1;index"`
	TagID       uint64        `gorm:"not null;uniqueIndex:uk_asset_tag,priority:2;index"`
	Source      TagBindSource `gorm:"type:varchar(16);not null;default:manual"`
	Confidence  float32       `gorm:"default:1"`
	BoundAt     time.Time     `gorm:"autoCreateTime"`
	BoundBy     string        `gorm:"type:varchar(64)"`

	AssetData AssetData `gorm:"foreignKey:AssetDataID"`
	Tag       TagNode   `gorm:"foreignKey:TagID"`
}

func (AssetDataTag) TableName() string { return "asset_data_tag" }

// ESSyncOutbox 可靠同步 ES（Outbox 模式，性能与一致性）
type ESSyncOutbox struct {
	ID          uint64    `gorm:"primaryKey;autoIncrement"`
	EntityType  string    `gorm:"type:varchar(32);not null;index:idx_outbox_pending,priority:1;comment:raw_data/asset_data"`
	EntityID    uint64    `gorm:"not null;index"`
	EntityUUID  string    `gorm:"type:char(36);not null;index"`
	Op          string    `gorm:"type:varchar(16);not null;comment:index/update/delete"`
	Payload     []byte    `gorm:"type:jsonb;not null;comment:ES 文档 JSON"`
	Status      string    `gorm:"type:varchar(16);not null;default:pending;index:idx_outbox_pending,priority:2"`
	RetryCount  int32     `gorm:"default:0"`
	LastError   string    `gorm:"type:text"`
	CreatedAt   time.Time `gorm:"autoCreateTime;index"`
	ProcessedAt *time.Time
}

func (ESSyncOutbox) TableName() string { return "es_sync_outbox" }
