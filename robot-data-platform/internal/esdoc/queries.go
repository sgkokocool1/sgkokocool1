package esdoc

import (
	"fmt"
	"strings"

	"github.com/sgkokocool1/sgkokocool1/robot-data-platform/internal/model"
)

// 索引名常量
const (
	IndexRawDataRecords   = "raw_data_records"
	IndexAssetDataRecords = "asset_data_records"
)

// TagFilter 标签筛选：大类之间 OR，同一大类内多选 AND
// 例：scene=[kitchen, table_a] AND task=[pick_red_block] → 命中同时含厨房+桌A 或 含抓红块 的数据
type TagFilter map[string][]string

// BuildTagQuery 构建 ES bool 查询
// - 每个 key（大类）对应一个 should 子句
// - 子句内对该大类下所有 path 做 must（AND）
// - 大类之间 minimum_should_match=1（OR）
func BuildTagQuery(groups TagFilter) map[string]interface{} {
	should := make([]map[string]interface{}, 0, len(groups))
	for _, paths := range groups {
		if len(paths) == 0 {
			continue
		}
		must := make([]map[string]interface{}, 0, len(paths))
		for _, p := range paths {
			must = append(must, termTagPath(model.NormalizeTagPath(p)))
		}
		should = append(should, map[string]interface{}{
			"bool": map[string]interface{}{"must": must},
		})
	}
	if len(should) == 0 {
		return map[string]interface{}{"match_all": map[string]interface{}{}}
	}
	if len(should) == 1 {
		return should[0]
	}
	return map[string]interface{}{
		"bool": map[string]interface{}{
			"should":               should,
			"minimum_should_match": 1,
		},
	}
}

// BuildTagSubtreeQuery 按树节点前缀检索（命中该节点及所有子孙绑定的数据）
func BuildTagSubtreeQuery(pathPrefix string) map[string]interface{} {
	prefix := model.NormalizeTagPath(pathPrefix)
	if prefix == "" {
		return map[string]interface{}{"match_all": map[string]interface{}{}}
	}
	return map[string]interface{}{
		"prefix": map[string]interface{}{"tag_paths": prefix},
	}
}

// BuildTagSubtreeQueryWithSlash 兼容带尾斜杠的前缀，避免 scene/indoor 误匹配 scene/indoor2
func BuildTagSubtreeQueryWithSlash(pathPrefix string) map[string]interface{} {
	prefix := model.NormalizeTagPath(pathPrefix)
	if prefix == "" {
		return map[string]interface{}{"match_all": map[string]interface{}{}}
	}
	return map[string]interface{}{
		"prefix": map[string]interface{}{"tag_paths": prefix + "/"},
	}
}

func termTagPath(path string) map[string]interface{} {
	return map[string]interface{}{
		"term": map[string]interface{}{"tag_paths": path},
	}
}

// NormalizeTagFilter 规范化筛选输入，按 path 首段自动归到大类
func NormalizeTagFilter(groups TagFilter) (TagFilter, error) {
	out := make(TagFilter, len(groups))
	for category, paths := range groups {
		category = strings.TrimSpace(category)
		normalized := make([]string, 0, len(paths))
		for _, p := range paths {
			p = model.NormalizeTagPath(p)
			if p == "" {
				continue
			}
			cat := model.TagCategoryFromPath(p)
			if category != "" && category != cat {
				return nil, fmt.Errorf("path %q 属于大类 %q，与筛选组 %q 不一致", p, cat, category)
			}
			normalized = append(normalized, p)
		}
		if len(normalized) == 0 {
			continue
		}
		key := category
		if key == "" {
			key = model.TagCategoryFromPath(normalized[0])
		}
		out[key] = append(out[key], normalized...)
	}
	return out, nil
}

/*
=== DSL 示例 ===

1. 大类 OR + 同大类 AND（scene 内厨房 AND 桌A，或 task 内抓红块）:
{
  "query": {
    "bool": {
      "should": [
        { "bool": { "must": [
          { "term": { "tag_paths": "scene/indoor/kitchen" } },
          { "term": { "tag_paths": "scene/indoor/table_a" } }
        ]}},
        { "bool": { "must": [
          { "term": { "tag_paths": "task/pick_red_block" } }
        ]}}
      ],
      "minimum_should_match": 1
    }
  }
}

2. 子树检索（选 scene/indoor 节点，命中其下所有叶子）:
{ "prefix": { "tag_paths": "scene/indoor/" } }

3. 看板聚合（按 path 首段分大类）:
GET raw_data_records/_search
{
  "size": 0,
  "aggs": {
    "by_status": { "terms": { "field": "status" } },
    "top_tag_paths": { "terms": { "field": "tag_paths", "size": 50 } }
  }
}
*/
