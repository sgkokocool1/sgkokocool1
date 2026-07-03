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

// CategoryLogic 同一大类内多选逻辑
type CategoryLogic string

const (
	CategoryLogicAnd CategoryLogic = "and" // 默认：组内全部命中
	CategoryLogicOr  CategoryLogic = "or"  // 组内任一命中
)

// TagCategoryFilter 单个大类的筛选条件
type TagCategoryFilter struct {
	Paths []string      `json:"paths"`
	Op    CategoryLogic `json:"op"` // and | or，默认 and
}

// TagFilter 标签筛选：大类之间 OR，同一大类内 op 由用户选择 AND/OR
type TagFilter map[string]TagCategoryFilter

// BuildTagQuery 构建 ES bool 查询
func BuildTagQuery(groups TagFilter) map[string]interface{} {
	should := make([]map[string]interface{}, 0, len(groups))
	for _, group := range groups {
		clause := buildCategoryClause(group)
		if clause != nil {
			should = append(should, clause)
		}
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

func buildCategoryClause(group TagCategoryFilter) map[string]interface{} {
	terms := make([]map[string]interface{}, 0, len(group.Paths))
	for _, p := range group.Paths {
		p = model.NormalizeTagPath(p)
		if p == "" {
			continue
		}
		terms = append(terms, termTagPath(p))
	}
	if len(terms) == 0 {
		return nil
	}
	if len(terms) == 1 {
		return terms[0]
	}
	if group.Op == CategoryLogicOr {
		return map[string]interface{}{
			"bool": map[string]interface{}{
				"should":               terms,
				"minimum_should_match": 1,
			},
		}
	}
	return map[string]interface{}{
		"bool": map[string]interface{}{"must": terms},
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

// BuildTagSubtreeQueryWithSlash 带尾斜杠前缀，避免 scene/indoor 误匹配 scene/indoor2
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
	for category, group := range groups {
		category = strings.TrimSpace(category)
		normalized := make([]string, 0, len(group.Paths))
		for _, p := range group.Paths {
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
		op := group.Op
		if op != CategoryLogicOr {
			op = CategoryLogicAnd
		}
		existing := out[key]
		existing.Paths = append(existing.Paths, normalized...)
		existing.Op = op
		out[key] = existing
	}
	return out, nil
}

/*
=== DSL 示例 ===

1. scene(AND) + task(OR)，大类之间 OR:
{
  "tag_filter": {
    "scene": { "paths": ["scene/indoor/kitchen", "scene/indoor/table_a"], "op": "and" },
    "task":  { "paths": ["task/pick_red_block", "task/place_blue_block"], "op": "or" }
  }
}
语义: (厨房 AND 桌A) OR (抓红 OR 放蓝)

2. 单大类组内 OR:
{ "tag_filter": { "scene": { "paths": ["scene/indoor/kitchen", "scene/outdoor"], "op": "or" } } }

3. 子树检索:
{ "prefix": { "tag_paths": "scene/indoor/" } }
*/
