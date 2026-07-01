# 数据结构分类 · 高频笔试 Coding 面试专题（Golang）

> 按数据结构组织的高频算法题专题，每章包含：**为何产生 → 解决什么问题 → 核心考点 → 高频题 → Go 解法 → 图示推演**

## 专题导航

| 序号 | 数据结构/算法范式 | 文档 | 核心思想 |
|------|------------------|------|----------|
| 01 | 数组 & 字符串 | [01-array-string.md](./01-array-string.md) | 连续内存、双指针、滑动窗口、前缀和 |
| 02 | 链表 | [02-linked-list.md](./02-linked-list.md) | 指针操作、快慢指针、虚拟头节点 |
| 03 | 栈 & 队列 | [03-stack-queue.md](./03-stack-queue.md) | LIFO/FIFO、单调栈、BFS 层序 |
| 04 | 哈希表 | [04-hash-map.md](./04-hash-map.md) | O(1) 查找、计数、去重、映射 |
| 05 | 二叉树 & BST | [05-binary-tree.md](./05-binary-tree.md) | 递归、DFS/BFS、中序性质 |
| 06 | 堆（优先队列） | [06-heap.md](./06-heap.md) | TopK、合并流、贪心调度 |
| 07 | 图 | [07-graph.md](./07-graph.md) | DFS/BFS、拓扑、最短路 |
| 08 | 二分查找 | [08-binary-search.md](./08-binary-search.md) | 有序性、答案空间二分 |
| 09 | 动态规划 | [09-dynamic-programming.md](./09-dynamic-programming.md) | 最优子结构、状态转移 |
| 10 | 回溯 | [10-backtracking.md](./10-backtracking.md) | 决策树、剪枝、排列组合 |
| 11 | 并查集 | [11-union-find.md](./11-union-find.md) | 连通分量、动态合并查询 |
| 12 | 字典树 Trie | [12-trie.md](./12-trie.md) | 前缀匹配、字符串集合 |

## 可运行代码

```bash
cd interview-prep/go
go test ./... -v
```

## 高清动图

所有算法核心思路均已制作为 **3840×2160（4K UHD）** 逐步推演动图，**每步停留 1 秒再跳转**（关键结果停 2 秒），存放于 `assets/gifs/`。

重新生成动图：

```bash
pip install -r interview-prep/scripts/requirements.txt
python3 interview-prep/scripts/generate_gifs.py
```

可在 `scripts/generate_gifs.py` 顶部调整 `FRAME_DURATION`（每跳秒数，默认 `1.0`）。

| 动图 | 对应题目 |
|------|----------|
| `01-sliding-window.gif` | LC3 无重复字符最长子串 |
| `01-three-sum.gif` | LC15 三数之和 |
| `02-reverse-list.gif` | LC206 反转链表 |
| `02-cycle-list.gif` | LC142 环形链表入口 |
| `03-monotonic-stack.gif` | LC739 每日温度 |
| `03-sliding-window-max.gif` | LC239 滑动窗口最大值 |
| `04-longest-consecutive.gif` | LC128 最长连续序列 |
| `05-tree-depth.gif` | LC104 二叉树最大深度 |
| `05-lca.gif` | LC236 最近公共祖先 |
| `06-heap-topk.gif` | LC215 第 K 大元素 |
| `07-islands-dfs.gif` | LC200 岛屿数量 |
| `07-topo-sort.gif` | LC207 课程表 |
| `08-rotated-binary-search.gif` | LC33 搜索旋转排序数组 |
| `09-kadane.gif` | LC53 最大子数组和 |
| `10-permute.gif` | LC46 全排列 |
| `11-union-find.gif` | LC684 冗余连接 |
| `12-trie-insert.gif` | LC208 实现 Trie |

## 如何使用本文档

1. **先读「为何产生」**：理解数据结构解决的历史/工程问题，面试时能讲清选型理由。
2. **记「核心考点」**：每类 3～5 个模板，比刷 100 道散题更高效。
3. **看「动图演示」**：逐步观察指针移动、栈变化、递归过程；建议对照推演表手画一遍。
4. **写 Go 代码**：`go/` 目录下为可运行实现，建议先闭卷再对照。

## 高频题速查（Top 30）

| 题号 | 题目 | 专题 | 难度 |
|------|------|------|------|
| 1 | 两数之和 | 哈希 | Easy |
| 3 | 无重复字符最长子串 | 滑动窗口 | Medium |
| 15 | 三数之和 | 双指针 | Medium |
| 19 | 删除链表倒数第 N 个 | 链表 | Medium |
| 20 | 有效括号 | 栈 | Easy |
| 21 | 合并两个有序链表 | 链表 | Easy |
| 33 | 搜索旋转排序数组 | 二分 | Medium |
| 46 | 全排列 | 回溯 | Medium |
| 53 | 最大子数组和 | DP/数组 | Medium |
| 56 | 合并区间 | 排序+数组 | Medium |
| 70 | 爬楼梯 | DP | Easy |
| 76 | 最小覆盖子串 | 滑动窗口 | Hard |
| 94 | 二叉树中序遍历 | 树 | Easy |
| 102 | 层序遍历 | BFS | Medium |
| 104 | 最大深度 | 树 | Easy |
| 121 | 买卖股票最佳时机 | DP | Easy |
| 128 | 最长连续序列 | 哈希 | Medium |
| 141 | 环形链表 | 快慢指针 | Easy |
| 142 | 环形链表入口 | 快慢指针 | Medium |
| 146 | LRU 缓存 | 哈希+双向链表 | Medium |
| 200 | 岛屿数量 | DFS/BFS | Medium |
| 206 | 反转链表 | 链表 | Easy |
| 215 | 数组第 K 大 | 堆 | Medium |
| 236 | 最近公共祖先 | 树 | Medium |
| 239 | 滑动窗口最大值 | 单调队列 | Hard |
| 300 | 最长递增子序列 | DP | Medium |
| 322 | 零钱兑换 | DP | Medium |
| 347 | 前 K 个高频元素 | 堆 | Medium |
| 416 | 分割等和子集 | DP/背包 | Medium |
| 560 | 和为 K 的子数组 | 前缀和+哈希 | Medium |
