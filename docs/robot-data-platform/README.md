# 机器人数据平台 · 设计文档索引

> **设计文档与代码实现分离。** 本目录为权威设计说明。

| 文档 | 内容 |
|------|------|
| [DESIGN.md](./DESIGN.md) | **主设计文档**（架构、TiDB 表、ES、检索、ER、展示） |
| [appendix-ddl.sql](./appendix-ddl.sql) | TiDB 建表 SQL |
| [appendix-es-mapping/](./appendix-es-mapping/) | Elasticsearch Mapping JSON |
| [appendix-tag-tree.yaml](./appendix-tag-tree.yaml) | 标签树配置（不进数据库） |

## 设计原则摘要

1. **TiDB** — 只管**数据路径**与流水线状态（轻量登记库）
2. **Elasticsearch** — 管检索元数据 + **标签**（`tag_paths` 唯一标签存储）
3. **标签树** — 配置文件 / 前端静态树，**不写入 TiDB**
4. **标签语义** — 大类 OR、同大类 AND

## 相关文档

| 文档 | 说明 |
|------|------|
| [LeRobot 数据流水线](../lerobot-workflow/README.md) | manifest ingest、数据集构建 |
| [数据统计看板设计](../lerobot-workflow/data-dashboard-design.md) | 看板统计补充 |
