package model

import (
	"time"

	"gorm.io/gorm"
)

// TagNode 树状标签节点（PG 存权威树结构，ES 存冗余 path 便于检索）
type TagNode struct {
	ID       uint64    `gorm:"primaryKey;autoIncrement"`
	ParentID *uint64   `gorm:"index;comment:父节点ID NULL 表示根"`
	Domain   TagDomain `gorm:"type:varchar(16);not null;uniqueIndex:uk_tag_domain_code,priority:1;index;comment:raw 场景标签 / asset 资产标签"`

	// 树定位
	Code  string `gorm:"type:varchar(128);not null;uniqueIndex:uk_tag_domain_code,priority:2;comment:节点编码 kitchen"`
	Name  string `gorm:"type:varchar(256);not null;comment:显示名 厨房"`
	Level int16  `gorm:"not null;default:0;index;comment:层级 0=根"`
	Path  string `gorm:"type:varchar(1024);not null;uniqueIndex;comment:物化路径 /scene/indoor/kitchen"`
	// Path 规则：/{level0}/{level1}/... 便于前缀查询子树

	FullName string `gorm:"type:varchar(512);comment:全路径名 场景/室内/厨房"`
	SortOrder int32 `gorm:"default:0;comment:同级排序"`
	IsLeaf   bool   `gorm:"default:false;index;comment:是否叶子（可绑定）"`
	IsActive bool   `gorm:"default:true;index;comment:是否启用"`

	Description string         `gorm:"type:text"`
	Extra       []byte         `gorm:"type:jsonb;comment:扩展属性"`
	CreatedAt   time.Time      `gorm:"autoCreateTime"`
	UpdatedAt   time.Time      `gorm:"autoUpdateTime"`
	DeletedAt   gorm.DeletedAt `gorm:"index"`

	Parent   *TagNode  `gorm:"foreignKey:ParentID"`
	Children []TagNode `gorm:"foreignKey:ParentID"`
}

func (TagNode) TableName() string { return "tag_node" }

// RawDataTag 原始数据 ↔ 标签 多对多
type RawDataTag struct {
	ID        uint64        `gorm:"primaryKey;autoIncrement"`
	RawDataID uint64        `gorm:"not null;uniqueIndex:uk_raw_tag,priority:1;index"`
	TagID     uint64        `gorm:"not null;uniqueIndex:uk_raw_tag,priority:2;index"`
	Source    TagBindSource `gorm:"type:varchar(16);not null;default:auto;comment:auto/manual/rule"`
	Confidence float32      `gorm:"default:1;comment:自动打标置信度 0-1"`
	BoundAt   time.Time     `gorm:"autoCreateTime"`
	BoundBy   string        `gorm:"type:varchar(64)"`

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
