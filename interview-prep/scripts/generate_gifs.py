#!/usr/bin/env python3
"""Generate high-quality algorithm animation GIFs for interview-prep docs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import matplotlib as mpl
import numpy as np
import imageio.v2 as imageio

# 中文字体（高清渲染）
mpl.rcParams["font.family"] = ["WenQuanYi Micro Hei", "DejaVu Sans", "sans-serif"]
mpl.rcParams["axes.unicode_minus"] = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "gifs")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Theme ──────────────────────────────────────────────────────────────────
BG       = "#0f1419"
PANEL    = "#1a2332"
TEXT     = "#e8edf4"
MUTED    = "#8b9cb3"
ACCENT   = "#3b82f6"
ACCENT2  = "#22d3ee"
SUCCESS  = "#34d399"
WARN     = "#fbbf24"
DANGER   = "#f87171"
PURPLE   = "#a78bfa"
HIGHLIGHT = "#f472b6"

# ── 4K 输出 & 播放速度配置 ─────────────────────────────────────────────────
TARGET_W, TARGET_H = 3840, 2160   # 4K UHD
DPI = 200
W, H = TARGET_W / DPI, TARGET_H / DPI   # 19.2 × 10.8 inch → 3840×2160 px
FONT_SCALE = TARGET_W / 1400            # 相对旧版缩放 (~2.74×)

FRAME_DURATION = 2.4        # 每帧停留秒数（慢速，便于阅读）
HOLD_STEP = 4                 # 普通步骤重复帧
HOLD_RESULT = 6               # 关键结果步骤
HOLD_FAST = 3                 # DFS 等细碎步骤
HOLD_LITE = 2                 # 全排列等长动画（避免过长）
FRAME_DURATION_LITE = 2.0     # 长动画每帧时长


def fs(size: float) -> float:
    """按 4K 缩放字号"""
    return size * FONT_SCALE


def lw(size: float) -> float:
    """按 4K 缩放线宽"""
    return size * FONT_SCALE


def setup_ax(title: str, subtitle: str = ""):
    fig, ax = plt.subplots(figsize=(W, H), facecolor=BG, dpi=DPI)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 54)
    ax.axis("off")
    ax.text(50, 51, title, ha="center", va="center", fontsize=fs(18),
            fontweight="bold", color=TEXT, family="sans-serif")
    if subtitle:
        ax.text(50, 47.5, subtitle, ha="center", va="center", fontsize=fs(11),
                color=MUTED, family="sans-serif")
    return fig, ax


def save_gif(name: str, frames: List[np.ndarray], duration: float = FRAME_DURATION):
    path = os.path.join(OUT_DIR, f"{name}.gif")
    imageio.mimsave(path, frames, duration=duration, loop=0, palettesize=256)
    print(f"  ✓ {path}  ({len(frames)} frames, {duration}s/frame, {TARGET_W}×{TARGET_H})")


def fig_to_array(fig) -> np.ndarray:
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    img = buf[:, :, :3].copy()
    plt.close(fig)
    return img


def hold(fig, n: int = HOLD_STEP) -> List[np.ndarray]:
    arr = fig_to_array(fig)
    return [arr] * n


def panel(ax, x, y, w, h, label: str, color=PANEL):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                       facecolor=color, edgecolor="#2d3f56", linewidth=lw(1.5), alpha=0.95)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h + 1.8, label, ha="center", fontsize=fs(9), color=MUTED)


def draw_array(ax, vals, y=28, highlight=None, window=None, pointers=None, title=""):
    n = len(vals)
    bw = min(7.5, 70 / n)
    start_x = 50 - (n * bw) / 2
    if title:
        ax.text(50, y + 12, title, ha="center", fontsize=fs(10), color=MUTED)
    for i, v in enumerate(vals):
        x = start_x + i * bw
        fc = PANEL
        ec = "#3d5270"
        if window and window[0] <= i <= window[1]:
            fc = "#1e3a5f"
            ec = ACCENT
        if highlight and i in highlight:
            fc = "#14532d"
            ec = SUCCESS
        rect = FancyBboxPatch((x, y), bw - 0.4, 8, boxstyle="round,pad=0.2,rounding_size=0.6",
                              facecolor=fc, edgecolor=ec, linewidth=lw(2))
        ax.add_patch(rect)
        ax.text(x + (bw - 0.4) / 2, y + 4, str(v), ha="center", va="center",
                fontsize=fs(13), fontweight="bold", color=TEXT)
        ax.text(x + (bw - 0.4) / 2, y - 3, str(i), ha="center", fontsize=fs(9), color=MUTED)
    if pointers:
        for name, idx, color in pointers:
            px = start_x + idx * bw + (bw - 0.4) / 2
            ax.annotate(name, xy=(px, y + 8.2), xytext=(px, y + 11.5),
                        ha="center", fontsize=fs(10), fontweight="bold", color=color,
                        arrowprops=dict(arrowstyle="->", color=color, lw=lw(1.8)))


def status_bar(ax, lines: List[str], y=6):
    panel(ax, 4, y - 2, 92, 10, "")
    for i, line in enumerate(lines):
        ax.text(8, y + 6 - i * 2.8, line, fontsize=fs(10), color=TEXT)


# ── Animations ───────────────────────────────────────────────────────────

def anim_sliding_window():
    """LC3 无重复字符最长子串"""
    s = list("abcabcbb")
    frames = []
    last, left, max_len = {}, 0, 0
    for right in range(len(s)):
        fig, ax = setup_ax("滑动窗口 · 无重复字符最长子串 (LC3)",
                           f'字符串 s = "{"".join(s)}"')
        c = s[right]
        dup = c in last and last[c] >= left
        if dup:
            left = last[c] + 1
        last[c] = right
        max_len = max(max_len, right - left + 1)
        hl = set(range(left, right + 1))
        draw_array(ax, s, y=30, highlight=hl, window=(left, right),
                   pointers=[("left", left, WARN), ("right", right, ACCENT2)])
        status_bar(ax, [
            f"step {right+1}: right→'{c}'" + ("  ⚠ 重复! left 跳转" if dup else ""),
            f"窗口 [{left},{right}] = \"{''.join(s[left:right+1])}\"",
            f"maxLen = {max_len}",
        ])
        frames.extend(hold(fig))
    save_gif("01-sliding-window", frames)


def anim_three_sum():
    nums = [-4, -1, -1, 0, 1, 2]
    frames = []
    n = len(nums)
    for i in range(n - 2):
        l, r = i + 1, n - 1
        while l < r:
            fig, ax = setup_ax("双指针 · 三数之和 (LC15)", "排序后固定 i，l/r 相向扫描")
            draw_array(ax, nums, y=32, highlight={i, l, r},
                       pointers=[("i", i, PURPLE), ("l", l, SUCCESS), ("r", r, DANGER)])
            s = nums[i] + nums[l] + nums[r]
            action = "sum < 0 → l++" if s < 0 else ("sum > 0 → r--" if s > 0 else "sum = 0 ✓ 记录")
            status_bar(ax, [
                f"nums[i]+nums[l]+nums[r] = {nums[i]}+{nums[l]}+{nums[r]} = {s}",
                action,
            ])
            frames.extend(hold(fig))
            if s == 0:
                l += 1
                r -= 1
                while l < r and nums[l] == nums[l - 1]:
                    l += 1
            elif s < 0:
                l += 1
            else:
                r -= 1
            if l >= r:
                break
    save_gif("01-three-sum", frames)


def anim_reverse_list():
    vals = [1, 2, 3, 4]
    frames = []
    prev_idx = -1
    cur_idx = 0
    next_map = {i: i + 1 for i in range(len(vals) - 1)}
    next_map[len(vals) - 1] = -1
    rev_next = {}

    def draw_nodes(ax, cur, prev, highlight=None):
        highlight = highlight or set()
        y = 30
        positions = {}
        for i, v in enumerate(vals):
            x = 18 + i * 16
            positions[i] = x
            fc = ACCENT if i == cur else (SUCCESS if i == prev else PANEL)
            if i in highlight:
                fc = "#7c3aed"
            circ = Circle((x, y), 3.5, facecolor=fc, edgecolor=TEXT, linewidth=lw(2))
            ax.add_patch(circ)
            ax.text(x, y, str(v), ha="center", va="center", fontsize=fs(14),
                    fontweight="bold", color=TEXT)
            ax.text(x, y - 6, f"node{i}", ha="center", fontsize=fs(8), color=MUTED)
            if i < len(vals) - 1:
                tgt = rev_next.get(i, next_map.get(i, i + 1))
                if tgt >= 0:
                    ax.annotate("", xy=(positions.get(tgt, 18 + tgt * 16) - 3.5, y),
                                xytext=(x + 3.5, y),
                                arrowprops=dict(arrowstyle="->", color=ACCENT2, lw=lw(2.2)))
        if prev_idx >= 0:
            ax.text(18 + prev * 16, y + 8, "prev", ha="center", color=SUCCESS, fontsize=fs(10))
        if cur_idx >= 0 and cur_idx < len(vals):
            ax.text(18 + cur * 16, y + 8, "cur", ha="center", color=ACCENT, fontsize=fs(10))

    step = 0
    cur = 0
    prev = -1
    while cur < len(vals):
        fig, ax = setup_ax("链表反转 · 三指针迭代 (LC206)", "cur.Next = prev; 整体前移")
        nxt = next_map.get(cur, -1) if cur not in rev_next else rev_next[cur]
        draw_nodes(ax, cur, prev, {cur})
        status_bar(ax, [
            f"step {step+1}: cur=node{cur}({vals[cur]}), prev={'nil' if prev<0 else f'node{prev}'}",
            f"执行: node{cur}.Next → {'nil' if prev<0 else f'node{prev}'}",
        ])
        frames.extend(hold(fig))
        rev_next[cur] = prev
        prev = cur
        cur = nxt if nxt >= 0 else len(vals)
        step += 1

    fig, ax = setup_ax("链表反转 · 完成", "返回 prev 作为新头节点")
    y = 30
    order = list(reversed(range(len(vals))))
    for j, i in enumerate(order):
        x = 18 + j * 16
        circ = Circle((x, y), 3.5, facecolor=SUCCESS, edgecolor=TEXT, linewidth=lw(2))
        ax.add_patch(circ)
        ax.text(x, y, str(vals[i]), ha="center", va="center", fontsize=fs(14),
                fontweight="bold", color=TEXT)
        if j < len(order) - 1:
            ax.annotate("", xy=(x + 16 - 3.5, y), xytext=(x + 3.5, y),
                        arrowprops=dict(arrowstyle="->", color=SUCCESS, lw=lw(2.5)))
    status_bar(ax, ["结果: 4 → 3 → 2 → 1"])
    frames.extend(hold(fig, HOLD_RESULT))
    save_gif("02-reverse-list", frames)


def anim_cycle_list():
    """Floyd 判环 + 找入口"""
    nodes = ["3", "2", "0", "-4"]
    # 0→1→2→3→1 (cycle at index 1)
    next_idx = [1, 2, 3, 1]
    frames = []

    def draw_cycle(ax, slow, fast, phase, extra_line=""):
        y = 32
        xs = [15, 35, 55, 75]
        for i, (x, v) in enumerate(zip(xs, nodes)):
            fc = PANEL
            if i == slow:
                fc = WARN
            if i == fast:
                fc = DANGER
            circ = Circle((x, y), 4, facecolor=fc, edgecolor=TEXT, linewidth=lw(2))
            ax.add_patch(circ)
            ax.text(x, y, v, ha="center", va="center", fontsize=fs(13),
                    fontweight="bold", color=TEXT)
            ni = next_idx[i]
            ax.annotate("", xy=(xs[ni] - 4, y), xytext=(x + 4, y),
                        arrowprops=dict(arrowstyle="->", color=ACCENT2, lw=lw(2)))
        # cycle arc
        ax.annotate("", xy=(35, 26), xytext=(75, 26),
                    arrowprops=dict(arrowstyle="->", color=PURPLE, lw=lw(1.5),
                                    connectionstyle="arc3,rad=-0.4"))
        labels = ["阶段: 快慢指针寻找相遇点", f"slow=node{slow}  fast=node{fast}", extra_line]
        if phase == 2:
            labels = ["阶段: 同步走找入口", f"ptr1=head  ptr2=meet", extra_line]
        status_bar(ax, labels)

    slow, fast = 0, 0
    step = 0
    for _ in range(6):
        fig, ax = setup_ax("环形链表入口 · Floyd 算法 (LC142)", "快指针 2 步，慢指针 1 步")
        draw_cycle(ax, slow, fast, 1)
        frames.extend(hold(fig))
        slow = next_idx[slow]
        fast = next_idx[next_idx[fast]]
        step += 1
        if slow == fast:
            break

    meet = slow
    p1, p2 = 0, meet
    for _ in range(4):
        fig, ax = setup_ax("环形链表入口 · 第二阶段", "head 与 meet 同速 → 入口")
        draw_cycle(ax, p1, p2, 2, f"ptr1=node{p1}  ptr2=node{p2}")
        frames.extend(hold(fig))
        if p1 == p2:
            fig2, ax2 = setup_ax("找到入口!", f"入口 = node{p1} (值 {nodes[p1]})")
            draw_cycle(ax2, p1, p1, 2, "✓ 相遇于环入口")
            frames.extend(hold(fig2, HOLD_RESULT))
            break
        p1 = next_idx[p1]
        p2 = next_idx[p2]
    save_gif("02-cycle-list", frames)


def anim_monotonic_stack():
    temps = [73, 74, 75, 71, 69, 72, 76, 73]
    frames = []
    stack = []
    ans = [0] * len(temps)
    for i, t in enumerate(temps):
        fig, ax = setup_ax("单调栈 · 每日温度 (LC739)", "栈存下标，递减；当前更大则弹栈")
        draw_array(ax, temps, y=32, highlight=set(stack + [i]),
                   pointers=[("i", i, ACCENT2)])
        # draw stack
        panel(ax, 72, 14, 24, 22, "单调栈 (下标)")
        for j, idx in enumerate(reversed(stack[-5:])):
            ax.text(84, 32 - j * 4, f"[{idx}] T={temps[idx]}", ha="center",
                    fontsize=fs(9), color=TEXT)
        popping = [j for j in stack if temps[i] > temps[j]]
        status_bar(ax, [
            f"day {i}: T={t}",
            f"弹栈: {popping if popping else '无'} → 填 ans = i-j",
            f"压入 {i}",
        ])
        frames.extend(hold(fig))
        while stack and temps[i] > temps[stack[-1]]:
            j = stack.pop()
            ans[j] = i - j
        stack.append(i)
    save_gif("03-monotonic-stack", frames)


def anim_sliding_max():
    nums = [1, 3, -1, -3, 5, 3, 6, 7]
    k = 3
    frames = []
    deque = []
    for i, x in enumerate(nums):
        while deque and nums[deque[-1]] <= x:
            deque.pop()
        deque.append(i)
        while deque and deque[0] <= i - k:
            deque.pop(0)
        if i >= k - 1:
            fig, ax = setup_ax("单调队列 · 滑动窗口最大值 (LC239)", f"k={k}")
            draw_array(ax, nums, y=32, window=(i - k + 1, i),
                       pointers=[("i", i, ACCENT2)])
            panel(ax, 4, 14, 40, 12, "双端队列 (存下标, 值递减)")
            dq_str = " ← ".join(f"[{j}]={nums[j]}" for j in deque)
            ax.text(24, 20, dq_str or "空", ha="center", fontsize=fs(9), color=TEXT)
            status_bar(ax, [
                f"窗口 [{i-k+1},{i}]",
                f"队头下标 {deque[0]} → max = {nums[deque[0]]}",
            ])
            frames.extend(hold(fig))
    save_gif("03-sliding-window-max", frames)


def anim_hash_consecutive():
    nums = [100, 4, 200, 1, 3, 2]
    s = set(nums)
    frames = []
    for x in sorted(s):
        if x - 1 in s:
            continue
        length = 1
        seq = [x]
        while x + length in s:
            seq.append(x + length)
            length += 1
        fig, ax = setup_ax("哈希集合 · 最长连续序列 (LC128)", "只从序列起点向后延伸")
        draw_array(ax, nums, y=32, highlight=set(nums.index(v) for v in seq if v in nums))
        status_bar(ax, [
            f"起点 {x}，延伸: {' → '.join(map(str, seq))}",
            f"长度 = {length}",
        ])
        frames.extend(hold(fig))
    save_gif("04-longest-consecutive", frames)


def anim_lca():
    r"""树结构:
          3
         / \
        5   1
       / \ / \
      6  2 0 8
        / \
       7   4
    """
    frames = []
    scenarios = [
        (5, 1, 3, "p=5, q=1 → 分居左右子树 → LCA=3"),
        (5, 4, 5, "p=5, q=4 → 同左子树 → 递归左侧"),
    ]
    tree = {
        3: (5, 1), 5: (6, 2), 1: (0, 8), 2: (7, 4)
    }
    pos = {3: (50, 40), 5: (35, 28), 1: (65, 28), 6: (26, 16),
           2: (44, 16), 0: (58, 16), 8: (72, 16), 7: (38, 4), 4: (50, 4)}
    val = {v: k for k, v in pos.items()}

    for p, q, ans, desc in scenarios:
        fig, ax = setup_ax("二叉树 · 最近公共祖先 (LC236)", desc)
        for node, (l, r) in tree.items():
            x, y = pos[node]
            for child in (l, r):
                cx, cy = pos[child]
                ax.plot([x, cx], [y - 2, cy + 2], color="#3d5270", lw=lw(2))
        for node, (x, y) in pos.items():
            fc = ACCENT if node == ans else (WARN if node in (p, q) else PANEL)
            circ = Circle((x, y), 3.2, facecolor=fc, edgecolor=TEXT, linewidth=lw(2))
            ax.add_patch(circ)
            ax.text(x, y, str(node), ha="center", va="center", fontsize=fs(11),
                    fontweight="bold", color=TEXT)
        status_bar(ax, [desc, f"LCA = node {ans}"])
        frames.extend(hold(fig, HOLD_RESULT))
    save_gif("05-lca", frames)


def anim_heap_topk():
    stream = [3, 2, 1, 5, 6, 4]
    k = 2
    heap = []
    frames = []
    for x in stream:
        heap.append(x)
        heap.sort()
        if len(heap) > k:
            removed = heap.pop(0)
        else:
            removed = None
        fig, ax = setup_ax("小根堆 · 第 K 大元素 (LC215)", f"维护大小为 k={k} 的小根堆")
        panel(ax, 30, 18, 40, 20, f"小根堆 (size≤{k})")
        # draw heap as tree-ish
        sorted_h = sorted(heap)
        for j, v in enumerate(sorted_h):
            y = 34 - j * 5
            circ = Circle((50, y), 3, facecolor=ACCENT if j == 0 else PANEL,
                          edgecolor=TEXT, linewidth=lw(2))
            ax.add_patch(circ)
            ax.text(50, y, str(v), ha="center", va="center", fontsize=fs(12),
                    fontweight="bold", color=TEXT)
            if j == 0:
                ax.text(58, y, "← 堆顶(第K大)", fontsize=fs(9), color=WARN)
        status_bar(ax, [
            f"插入 {x}" + (f", 弹出 {removed}" if removed is not None else ""),
            f"堆: {sorted_h}",
        ])
        frames.extend(hold(fig))
    save_gif("06-heap-topk", frames)


def anim_islands():
    grid = [
        list("110"),
        list("110"),
        list("001"),
    ]
    frames = []
    count = 0
    rows, cols = 3, 3
    g = [row[:] for row in grid]

    def draw_grid(highlight=None, flooded=None):
        highlight = highlight or set()
        flooded = flooded or set()
        for r in range(rows):
            for c in range(cols):
                x, y = 25 + c * 14, 36 - r * 12
                ch = g[r][c]
                fc = "#14532d" if (r, c) in flooded else (PANEL if ch == '0' else "#1e40af")
                if (r, c) in highlight:
                    fc = ACCENT2
                rect = FancyBboxPatch((x, y), 11, 9, boxstyle="round,pad=0.2,rounding_size=0.5",
                                      facecolor=fc, edgecolor="#3d5270", linewidth=lw(2))
                ax.add_patch(rect)
                ax.text(x + 5.5, y + 4.5, ch, ha="center", va="center",
                        fontsize=fs(16), fontweight="bold", color=TEXT)

    for r in range(rows):
        for c in range(cols):
            if g[r][c] == '1':
                count += 1
                flooded = set()
                stack = [(r, c)]
                step = 0
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cc < 0 or cr >= rows or cc >= cols or g[cr][cc] == '0':
                        continue
                    g[cr][cc] = '0'
                    flooded.add((cr, cc))
                    fig, ax = setup_ax("网格 DFS · 岛屿数量 (LC200)", f"发现第 {count} 个岛屿")
                    draw_grid(highlight={(cr, cc)}, flooded=flooded)
                    status_bar(ax, [
                        f"DFS step {step+1}: 淹没 ({cr},{cc})",
                        f"岛屿计数 = {count}",
                    ])
                    frames.extend(hold(fig, HOLD_FAST))
                    step += 1
                    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        stack.append((cr + dr, cc + dc))
    save_gif("07-islands-dfs", frames)


def anim_topo():
    """课程表: 0→1, 0→2, 1→3, 2→3"""
    edges = [(0, 1), (0, 2), (1, 3), (2, 3)]
    n = 4
    indeg = [0] * n
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[b].append(a)
        indeg[a] += 1
    q = [i for i in range(n) if indeg[i] == 0]
    seen = 0
    frames = []
    pos = {0: (25, 30), 1: (45, 18), 2: (65, 30), 3: (45, 42)}

    while q:
        u = q.pop(0)
        seen += 1
        fig, ax = setup_ax("拓扑排序 · 课程表 (LC207)", "入度 0 入队，消边")
        for a, b in edges:
            x1, y1 = pos[b]
            x2, y2 = pos[a]
            ax.annotate("", xy=(x2, y2 + 3), xytext=(x1, y1 - 3),
                        arrowprops=dict(arrowstyle="->", color="#3d5270", lw=lw(2)))
        for node, (x, y) in pos.items():
            fc = SUCCESS if node == u else (PANEL if indeg[node] > 0 else WARN)
            circ = Circle((x, y), 4, facecolor=fc, edgecolor=TEXT, linewidth=lw(2))
            ax.add_patch(circ)
            ax.text(x, y, str(node), ha="center", va="center", fontsize=fs(12),
                    fontweight="bold", color=TEXT)
            ax.text(x, y - 7, f"in={indeg[node]}", ha="center", fontsize=fs(8), color=MUTED)
        status_bar(ax, [
            f"出队 course {u}",
            f"已处理 {seen}/{n} 门课",
        ])
        frames.extend(hold(fig))
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    save_gif("07-topo-sort", frames)


def anim_rotated_search():
    nums = [4, 5, 6, 7, 0, 1, 2]
    target = 0
    left, right = 0, len(nums) - 1
    frames = []
    while left <= right:
        mid = left + (right - left) // 2
        fig, ax = setup_ax("二分查找 · 旋转排序数组 (LC33)", f"target = {target}")
        hl = {left, mid, right}
        ptrs = [("L", left, SUCCESS), ("M", mid, WARN), ("R", right, DANGER)]
        draw_array(ax, nums, y=32, highlight=hl, pointers=ptrs)
        ordered_left = nums[left] <= nums[mid]
        in_left = nums[left] <= target < nums[mid]
        if nums[mid] == target:
            action = f"命中! index = {mid}"
        elif ordered_left:
            action = f"左半有序; target{'在' if in_left else '不在'}左 → {'R=M-1' if in_left else 'L=M+1'}"
        else:
            action = "右半有序; 相应收缩"
        status_bar(ax, [f"mid={mid}, nums[mid]={nums[mid]}", action])
        frames.extend(hold(fig))
        if nums[mid] == target:
            break
        if ordered_left:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    save_gif("08-rotated-binary-search", frames)


def anim_kadane():
    nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    frames = []
    cur, best = nums[0], nums[0]
    start = 0
    best_range = (0, 0)
    cur_start = 0
    for i in range(1, len(nums)):
        fig, ax = setup_ax("Kadane · 最大子数组和 (LC53)", "cur = max(x, cur+x)")
        if cur + nums[i] > nums[i]:
            cur = cur + nums[i]
        else:
            cur = nums[i]
            cur_start = i
        if cur > best:
            best = cur
            best_range = (cur_start, i)
        draw_array(ax, nums, y=32, window=best_range,
                   highlight=set(range(best_range[0], best_range[1] + 1)))
        status_bar(ax, [
            f"i={i}, x={nums[i]}",
            f"cur={cur}, best={best}",
            f"最优区间 [{best_range[0]},{best_range[1]}]",
        ])
        frames.extend(hold(fig))
    save_gif("09-kadane", frames)


def anim_permute():
    nums = [1, 2, 3]
    frames = []
    used = [False] * 3
    path = []

    def capture(action):
        fig, ax = setup_ax("回溯 · 全排列 (LC46)", action)
        panel(ax, 8, 22, 35, 16, "决策树 path")
        ax.text(25, 30, " → ".join(map(str, path)) if path else "[]",
                ha="center", fontsize=fs(14), color=ACCENT2, fontweight="bold")
        draw_array(ax, nums, y=10, highlight=set(i for i, u in enumerate(used) if u))
        status_bar(ax, [action, f"depth={len(path)}/3"])
        frames.extend(hold(fig, HOLD_LITE))

    def dfs():
        if len(path) == 3:
            capture(f"✓ 记录排列 {path}")
            return
        for i in range(3):
            if used[i]:
                continue
            used[i] = True
            path.append(nums[i])
            capture(f"选择 nums[{i}]={nums[i]}")
            dfs()
            path.pop()
            used[i] = False
            capture(f"撤销 nums[{i}]")

    dfs()
    save_gif("10-permute", frames, duration=FRAME_DURATION_LITE)


def anim_union_find():
    edges = [[1, 2], [1, 3], [2, 3]]
    parent = {1: 1, 2: 2, 3: 3}
    frames = []

    def draw_uf(highlight_edge=None):
        pos = {1: (30, 30), 2: (50, 20), 3: (70, 30)}
        for a, b in [(1, 2), (1, 3)]:
            if parent[a] == parent[b] or (a, b) == highlight_edge or (b, a) == highlight_edge:
                x1, y1 = pos[a]
                x2, y2 = pos[b]
                ax.plot([x1, x2], [y1, y2], color=ACCENT2, lw=lw(2), alpha=0.6)
        for node, (x, y) in pos.items():
            root = parent[node]
            circ = Circle((x, y), 4, facecolor=PANEL, edgecolor=TEXT, linewidth=lw(2))
            ax.add_patch(circ)
            ax.text(x, y, str(node), ha="center", va="center", fontsize=fs(13),
                    fontweight="bold", color=TEXT)
            ax.text(x, y - 7, f"root={root}", ha="center", fontsize=fs(8), color=MUTED)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        a, b = e
        ra, rb = find(a), find(b)
        fig, ax = setup_ax("并查集 · 冗余连接 (LC684)", f"处理边 [{a},{b}]")
        draw_uf((a, b))
        if ra == rb:
            status_bar(ax, [f"Find({a})={ra}, Find({b})={rb}", f"⚠ 同集! 冗余边 [{a},{b}]"])
            frames.extend(hold(fig, HOLD_RESULT))
            break
        else:
            parent[rb] = ra
            status_bar(ax, [f"Union({a},{b})", f"parent[{b}]={ra}"])
            frames.extend(hold(fig))
    save_gif("11-union-find", frames)


def anim_trie():
    words = ["cat", "car", "dog"]
    frames = []
    # simple trie visualization
    trie = {}
    for w in words:
        node = trie
        for ch in w:
            if ch not in node:
                node[ch] = {}
            node = node[ch]
        node["#"] = True
        fig, ax = setup_ax("字典树 Trie · 插入过程 (LC208)", f'插入 "{w}"')
        # draw trie tree
        y = 40
        ax.text(15, y, "root", fontsize=fs(11), color=TEXT,
                bbox=dict(boxstyle="round", facecolor=PANEL, edgecolor=ACCENT))
        # BFS layout
        positions = {"": (15, y)}
        level_nodes = [("", trie)]
        x_slots = {0: [15], 1: [8, 22, 35], 2: [5, 11, 17, 25, 31]}
        drawn = set()

        def draw_trie(t, prefix, depth, slot_idx):
            if depth > 2:
                return
            children = [k for k in t if k != "#"]
            for i, ch in enumerate(sorted(children)):
                px = 15 + depth * 22
                py = y - depth * 12 - i * 3
                if prefix + ch not in drawn:
                    drawn.add(prefix + ch)
                    end = "#" in t[ch]
                    fc = SUCCESS if end else PANEL
                    ax.text(px, py, ch + ("*" if end else ""), fontsize=fs(10), color=TEXT,
                            bbox=dict(boxstyle="round", facecolor=fc, edgecolor=ACCENT2))
                    if depth > 0:
                        ax.annotate("", xy=(px - 2, py + 1), xytext=(px - 18, py + 10),
                                    arrowprops=dict(arrowstyle="->", color="#3d5270", lw=lw(1.2)))
                    draw_trie(t[ch], prefix + ch, depth + 1, i)

        draw_trie(trie, "", 0, 0)
        status_bar(ax, [f'完成插入 "{w}"', "带 * 为单词结尾"])
        frames.extend(hold(fig))
    save_gif("12-trie-insert", frames)


def anim_tree_depth():
    """LC104 最大深度递归展开"""
    frames = []
    pos = {3: (50, 42), 9: (30, 28), 20: (70, 28), 15: (60, 14), 7: (80, 14)}
    edges = [(3, 9), (3, 20), (20, 15), (20, 7)]
    steps = [
        (3, "根节点 depth=1"),
        (9, "左子 9 depth=2 → 返回 2"),
        (20, "右子 20 depth=2"),
        (15, "20.left 15 depth=3 → 返回 3"),
        (7, "20.right 7 depth=3 → 返回 3"),
        (3, "max(2,3)+1 = 3 ✓"),
    ]
    for node, msg in steps:
        fig, ax = setup_ax("递归 DFS · 二叉树最大深度 (LC104)", msg)
        for a, b in edges:
            x1, y1 = pos[a]
            x2, y2 = pos[b]
            ax.plot([x1, x2], [y1 - 2, y2 + 2], color="#3d5270", lw=lw(2.5))
        for n, (x, y) in pos.items():
            fc = ACCENT if n == node else PANEL
            circ = Circle((x, y), 3.5, facecolor=fc, edgecolor=TEXT, linewidth=lw(2))
            ax.add_patch(circ)
            ax.text(x, y, str(n), ha="center", va="center", fontsize=fs(12),
                    fontweight="bold", color=TEXT)
        status_bar(ax, [msg, "maxDepth = 3"])
        frames.extend(hold(fig))
    save_gif("05-tree-depth", frames)


def main():
    print("Generating HD algorithm GIFs...")
    anim_sliding_window()
    anim_three_sum()
    anim_reverse_list()
    anim_cycle_list()
    anim_monotonic_stack()
    anim_sliding_max()
    anim_hash_consecutive()
    anim_tree_depth()
    anim_lca()
    anim_heap_topk()
    anim_islands()
    anim_topo()
    anim_rotated_search()
    anim_kadane()
    anim_permute()
    anim_union_find()
    anim_trie()
    print(f"\nDone! Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
