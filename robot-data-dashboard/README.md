# Robot Data Dashboard

机器人原始数据统计大看板 — FastAPI + PostgreSQL + React 代码框架。

设计文档：[data-dashboard-design.md](../docs/lerobot-workflow/data-dashboard-design.md)

## 目录结构

```
robot-data-dashboard/
├── docker-compose.yml      # 一键启动 db + api + web
├── api/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py       # SQLAlchemy 模型
│   │   ├── schemas.py      # Pydantic 响应
│   │   ├── routers/        # REST API
│   │   └── services/       # 统计与同步逻辑
│   └── scripts/
│       └── sync_stats_db.py
└── web/                    # React + Ant Design + ECharts
    └── src/pages/          # 总览 / 分布 / 流水线 / Episodes / 存储
```

## 快速启动（Docker）

```bash
cd robot-data-dashboard
cp .env.example .env
# 编辑 DATA_ROOT 指向你的 /data 目录

docker compose up -d --build
# 首次同步数据
docker compose run --rm sync

open http://localhost:3000
```

API 文档：http://localhost:8080/docs

## 本地开发

### 后端

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://robot:robot_secret@localhost:5432/robot_stats
export DATA_ROOT=/data
uvicorn app.main:app --reload --port 8080
```

### 前端

```bash
cd web
npm install
npm run dev
```

### 同步 manifest

```bash
cd api
python scripts/sync_stats_db.py --data-root /data

# ingest 完成后记录 job
python scripts/sync_stats_db.py --event ingest --job-type daily_ingest --report /data/builds/xxx/import_report.json
```

## 与现有流水线集成

在 `daily_ingest.sh` 末尾追加：

```bash
python3 /data/dashboard/api/scripts/sync_stats_db.py \
  --data-root "$DATA_ROOT" \
  --event ingest \
  --job-type daily_ingest
```

在 `build_lerobot_dataset.py` 完成后：

```bash
python3 /data/dashboard/api/scripts/sync_stats_db.py \
  --data-root /data \
  --event build \
  --job-type build_weekly \
  --report "$LOG_DIR/import_report.json"
```

cron 每 5 分钟全量同步：

```cron
*/5 * * * * root cd /data/dashboard/api && python scripts/sync_stats_db.py
```

## API 端点

| 路径 | 说明 |
|------|------|
| GET /api/v1/overview | 总览 KPI |
| GET /api/v1/distribution/source | 按来源分布 |
| GET /api/v1/funnel | 处理漏斗 |
| GET /api/v1/trend/daily | 日趋势 |
| GET /api/v1/jobs | 任务流列表 |
| GET /api/v1/episodes | Episode 分页 |
| GET /api/v1/storage | 存储快照 |
| POST /api/v1/sync/trigger | 手动同步 |

## 页面

- `/` 总览大看板（KPI + 饼图 + 漏斗 + 趋势 + 任务流）
- `/distribution` 数据分布
- `/pipeline` 处理流水线
- `/episodes` Episode 明细筛选
- `/storage` 存储趋势
