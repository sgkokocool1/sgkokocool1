# 原始数据 & 资产数据设计（已迁移）

> **本文件已废弃为独立设计文档。** 权威设计请阅读：

## 主设计文档

📄 **[docs/robot-data-platform/DESIGN.md](../../docs/robot-data-platform/DESIGN.md)**

包含：架构、PostgreSQL 表结构、ES 索引、检索设计、ER 图、展示设计（UI/看板）。

## 附录

| 文件 | 说明 |
|------|------|
| [appendix-ddl.sql](../../docs/robot-data-platform/appendix-ddl.sql) | PostgreSQL 建表 SQL |
| [appendix-es-mapping/](../../docs/robot-data-platform/appendix-es-mapping/) | ES Mapping JSON |

## 代码实现（非设计）

实现代码位于 `robot-data-platform/internal/`，以设计文档为准演进：

- `internal/model/` — GORM 模型
- `internal/esdoc/` — ES 文档结构与查询构建

## 索引

[docs/robot-data-platform/README.md](../../docs/robot-data-platform/README.md)
