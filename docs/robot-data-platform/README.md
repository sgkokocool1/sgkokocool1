# 机器人数据平台 · 设计文档索引

> **设计文档与代码实现分离。** 本目录为权威设计说明。

| 文档 | 内容 |
|------|------|
| [DESIGN.md](./DESIGN.md) | v1.x 设计（路径表 + ES 标签，**建议阅后对照 v2 调研**） |
| [industry-benchmark-and-redesign.md](./industry-benchmark-and-redesign.md) | **业内方案调研 + v2 架构建议（推荐阅读）** |
| [end-to-end-business-workflow.md](./end-to-end-business-workflow.md) | **端到端业务流程举例**（采集→训练全链路） |
| [飞书文档-机器人数据平台设计.md](./飞书文档-机器人数据平台设计.md) | **飞书粘贴版**（正文 + 配图说明） |
| [images/](./images/) | **配图 PNG**（9 张，复制到飞书） |
| [diagrams/](./diagrams/) | Mermaid 图源，`render.sh` 重新出图 |
| [appendix-task-stats.sql](./appendix-task-stats.sql) | 任务完成度统计 SQL |
| [appendix-es-mapping/](./appendix-es-mapping/) | Elasticsearch Mapping JSON |
| [appendix-tag-tree.yaml](./appendix-tag-tree.yaml) | 标签树配置（不进数据库） |

## 设计原则摘要

1. **TiDB** — 只管**数据路径**与流水线状态（轻量登记库）
2. **Elasticsearch** — 管检索元数据 + **标签**（`tag_paths` 唯一标签存储）
3. **标签树** — 配置文件 / 前端静态树，**不写入 TiDB**
4. **标签语义** — 大类之间 OR；**同大类内 AND/OR 用户可选**

## 相关文档

| 文档 | 说明 |
|------|------|
| [LeRobot 数据流水线](../lerobot-workflow/README.md) | manifest ingest、数据集构建 |
| [数据统计看板设计](../lerobot-workflow/data-dashboard-design.md) | 看板统计补充 |
