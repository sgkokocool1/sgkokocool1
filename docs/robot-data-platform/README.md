# 机器人数据平台 · 设计文档索引

> **设计文档与代码实现分离。** 本目录为权威设计说明；代码实现见仓库 `robot-data-platform/`、`robot-data-dashboard/`。

| 文档 | 内容 |
|------|------|
| [DESIGN.md](./DESIGN.md) | **主设计文档**（架构、表结构、ES、检索、ER 图、展示设计） |
| [附录：DDL](./appendix-ddl.sql) | PostgreSQL 建表 SQL（可直接执行） |
| [附录：ES Mapping](./appendix-es-mapping/) | Elasticsearch 索引 Mapping JSON |

## 相关文档

| 文档 | 说明 |
|------|------|
| [LeRobot 数据流水线](../lerobot-workflow/README.md) | manifest 日终 ingest、周构建、训练流程 |
| [数据统计看板设计](../lerobot-workflow/data-dashboard-design.md) | 看板统计层（episodes/jobs）补充设计 |

## 设计原则摘要

1. **PostgreSQL** 管事务、状态机、标签树权威结构
2. **Elasticsearch** 管全文检索、标签组合过滤、看板聚合
3. **Outbox** 异步同步 PG → ES，最终一致
4. **标签**：大类之间 OR，同大类内 AND；ES 仅存 `tag_paths`
