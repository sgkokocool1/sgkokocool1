package esdoc

// 索引名常量
const (
	IndexRawDataRecords   = "raw_data_records"
	IndexAssetDataRecords = "asset_data_records"
	IndexTagSuggest       = "tag_suggest" // 可选：标签自动补全
)

// QueryExamples ES 检索 DSL 示例（Go 中可用 olivier/easing 或官方 esapi 构造）

/*
=== 1. 按状态 + 来源过滤原始数据（看板统计） ===
GET raw_data_records/_search
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "status": "finished" } },
        { "term": { "source_type": "collected" } },
        { "range": { "created_at": { "gte": "2025-07-01", "lte": "2025-07-31" } } }
      ]
    }
  },
  "aggs": {
    "by_data_type": { "terms": { "field": "data_type", "size": 20 } },
    "by_status": { "terms": { "field": "status" } }
  }
}

=== 2. 树状标签：检索某节点及所有子孙（prefix on tag_paths） ===
// 标签树 path=/scene/indoor/kitchen 时，子节点 path 均以该前缀开头
// 写入时已冗余祖先 path 到 tag_paths
GET raw_data_records/_search
{
  "query": {
    "bool": {
      "filter": [
        { "prefix": { "tag_paths": "/scene/indoor/kitchen" } }
      ]
    }
  }
}

=== 3. 多标签 AND（nested 精确） ===
GET raw_data_records/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "nested": {
            "path": "tags",
            "query": { "term": { "tags.path": "/task/pick_red_block" } }
          }
        },
        {
          "nested": {
            "path": "tags",
            "query": { "term": { "tags.path": "/scene/indoor" } }
          }
        }
      ]
    }
  }
}

=== 4. 标签文本模糊搜 ===
GET raw_data_records/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "tag_text": "厨房 抓取" } }
      ],
      "filter": [
        { "terms": { "status": ["finished", "correct"] } }
      ]
    }
  }
}

=== 5. 资产：查某批 raw 生成了哪些资产 ===
GET asset_data_records/_search
{
  "query": {
    "term": { "source_raw_data_ids": 12345 }
  }
}

=== 6. 资产标签聚合（看板） ===
GET asset_data_records/_search
{
  "size": 0,
  "aggs": {
    "top_tags": {
      "terms": { "field": "tag_codes", "size": 50 }
    },
    "by_asset_type": {
      "terms": { "field": "asset_type" }
    },
    "success_vs_fail": {
      "filters": {
        "filters": {
          "success": { "term": { "status": "success" } },
          "failure": { "term": { "status": "failure" } }
        }
      }
    }
  }
}
*/
