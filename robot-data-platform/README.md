# Robot Data Platform

原始数据 & 资产数据 数据层：GORM 模型 + Elasticsearch 文档结构。

设计文档（中文详细）：[docs/raw-asset-es-design.md](docs/raw-asset-es-design.md)

## 模块

| 路径 | 内容 |
|------|------|
| `internal/model/` | GORM 表：raw_data、asset_data、tag_node、绑定表、outbox |
| `internal/esdoc/` | ES Mapping、Record 结构、构建器、查询 DSL 示例 |

## 快速使用

```go
import (
    "github.com/sgkokocool1/sgkokocool1/robot-data-platform/internal/model"
    "github.com/sgkokocool1/sgkokocool1/robot-data-platform/internal/esdoc"
)

// 迁移
model.AutoMigrateAll(db)

// 构建 ES 文档
doc := esdoc.BuildRawDataRecord(raw, tags, binds)
// index to raw_data_records with _id = raw.UUID
```

## 与流水线关系

参见 [lerobot-workflow](../docs/lerobot-workflow/README.md) 与 [data-dashboard-design](../docs/lerobot-workflow/data-dashboard-design.md)。
