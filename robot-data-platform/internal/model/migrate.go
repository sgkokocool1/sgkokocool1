package model

import (
	"gorm.io/gorm"
)

// AutoMigrateAll 创建/更新所有表
func AutoMigrateAll(db *gorm.DB) error {
	return db.AutoMigrate(
		&RawData{},
		&AssetData{},
		&AssetDataRawSource{},
		&TagNode{},
		&RawDataTag{},
		&AssetDataTag{},
		&ProcessingLog{},
		&ESSyncOutbox{},
	)
}
