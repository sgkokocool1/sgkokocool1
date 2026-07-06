-- 数据任务完成度统计 SQL 示例
-- 设计文档：docs/robot-data-platform/DESIGN.md §7.7

-- 1. 单条数据任务完成度
SELECT
    entity_id,
    storage_path,
    COUNT(*) AS total_tasks,
    SUM(CASE WHEN status IN ('success', 'skipped') THEN 1 ELSE 0 END) AS completed_tasks,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_tasks,
    ROUND(100.0 * SUM(CASE WHEN status IN ('success', 'skipped') THEN 1 ELSE 0 END) / COUNT(*), 1) AS progress_pct
FROM data_task_rel
WHERE entity_type = 'raw_data' AND entity_id = ?;

-- 2. 单条数据各任务明细（详情页进度条）
SELECT task_code, status, started_at, finished_at, duration_ms, error_message
FROM data_task_rel
WHERE entity_type = 'raw_data' AND entity_id = ?
ORDER BY sort_order;

-- 3. 按任务类型统计全局分布
SELECT task_code, status, COUNT(*) AS cnt
FROM data_task_rel
GROUP BY task_code, status
ORDER BY task_code, status;

-- 4. 未完成全部任务的数据
SELECT entity_id, storage_path,
    SUM(CASE WHEN status IN ('success', 'skipped') THEN 1 ELSE 0 END) AS done,
    COUNT(*) AS total
FROM data_task_rel
WHERE entity_type = 'raw_data'
GROUP BY entity_id, storage_path
HAVING done < total;

-- 5. 某任务失败的数据列表
SELECT storage_path, error_message, finished_at
FROM data_task_rel
WHERE task_code = 'clean' AND status = 'failed'
ORDER BY finished_at DESC;
