#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snake.py — 经典贪吃蛇小游戏

仅依赖 Python 标准库（tkinter），单文件即可运行，无任何第三方依赖。
作者：Ayase Eli (AyaseEli-Bing)
版本：0.11.0
许可：MIT

运行方式：
    python3 snake_game.py

0.11.0 新增内容（与 0.10.21 兼容）：
    • 障碍物 + 多关卡：每关随机生成砖块障碍，蛇身达到目标长度即升级
    • 特殊食物：金豆（+50 分，立即缩短蛇身 3 节）
    • 特殊食物：辣豆（+30 分，8 秒内左右/上下控制方向互换）
    • 撞障碍 = 立即死亡
"""

from __future__ import annotations

import random
import sys
import tkinter as tk
from collections import deque
from tkinter import font as tkfont

__version__ = "0.11.0"


# ============================================================================
# 常量（可直接调整以改变游戏参数）
# ============================================================================
CELL = 22                    # 单格像素
GRID_W, GRID_H = 26, 22      # 网格宽高（格子数）
HEADER_H = 56                # 顶部状态栏高度（像素）
INFO_W = 4                   # 状态栏内边距

INITIAL_DELAY_MS = 110       # 起手帧间隔（毫秒），数值越小越快
MIN_DELAY_MS = 45            # 速度上限
SPEEDUP_EVERY = 5            # 每吃 N 个食物提速一次
SPEEDUP_STEP_MS = 6          # 每次提速缩短的毫秒数

FOOD_SCORE = 10              # 每个普通食物的得分
GOLD_SCORE = 50              # 金豆得分
HOT_SCORE = 30               # 辣豆得分
GOLD_SHORTEN = 3             # 吃到金豆蛇身缩短节数（最短 2 节）
HOT_DURATION_MS = 8000       # 辣豆导致方向反转的持续时间
SPECIAL_SPAWN_CHANCE = 0.06  # 每帧无特殊食物时生成特殊食物的概率

# 障碍 / 关卡
LEVEL_BASE_OBSTACLES = 6     # 第 1 关障碍数
LEVEL_OBSTACLE_STEP = 4      # 每升 1 关额外增加的障碍数
LEVEL_BASE_TARGET = 14       # 第 1 关通关需达到的蛇长度
LEVEL_TARGET_STEP = 2        # 每升 1 关增加的通关长度要求

BG_COLOR = "#0d1422"         # 背景色
HEADER_COLOR = "#101a2e"     # 状态栏背景
GRID_COLOR = "#172238"       # 网格线
SNAKE_HEAD = "#7be88a"       # 蛇头颜色
SNAKE_BODY_LIGHT = "#4dd066"
SNAKE_BODY_DARK = "#2a9a47"
FOOD_COLOR_A = "#ff5577"
FOOD_COLOR_B = "#ffb347"
GOLD_COLOR_A = "#ffd166"     # 金豆主色
GOLD_COLOR_B = "#ffea8a"     # 金豆高光
HOT_COLOR_A = "#b76aff"      # 辣豆主色
HOT_COLOR_B = "#ff77ff"      # 辣豆高光
OBSTACLE_COLOR = "#5b6b8a"   # 障碍色
OBSTACLE_EDGE = "#2b3654"    # 障碍边缘色
INVERT_TINT = "#ff5577"      # 反转状态提示色
TEXT_COLOR = "#e6edf7"
SUBTLE_COLOR = "#7d8aa3"
ACCENT_COLOR = "#7be88a"
DANGER_COLOR = "#ff5d6c"


# ============================================================================
# 键盘映射
# ============================================================================
DIRECTION_KEYS = {
    "Up":    (0, -1),
    "Down":  (0,  1),
    "Left":  (-1, 0),
    "Right": (1,  0),
    "w": (0, -1), "W": (0, -1),
    "s": (0,  1), "S": (0,  1),
    "a": (-1, 0), "A": (-1, 0),
    "d": (1,  0), "D": (1,  0),
}


# ============================================================================
# 游戏主类
# ============================================================================
class SnakeGame:
    """经典贪吃蛇小游戏（GUI 实现）。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"Snake · v{__version__}")
        self.root.resizable(False, False)

        width = GRID_W * CELL
        height = GRID_H * CELL + HEADER_H
        self.canvas = tk.Canvas(
            root,
            width=width,
            height=height,
            bg=BG_COLOR,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        # 字体
        self.title_font = tkfont.Font(family="Menlo", size=13, weight="bold")
        self.small_font = tkfont.Font(family="Menlo", size=10)

        # 绑定按键
        for key in ("<Key>",):
            self.root.bind(key, self.on_key)
        self.root.bind("<Escape>", lambda _e: self.quit_game())
        # 即时获得焦点，这样按键即生效
        self.root.focus_set()

        # 状态
        self.high_score = 0
        self.delay_ms = INITIAL_DELAY_MS
        self._frame_id: str | None = None
        self._food_pulse = 0.0
        self._after_reset_id: str | None = None

        self.reset_state()
        self.draw()
        self.tick()

    # ----------------------------------------------------------------------
    # 状态
    # ----------------------------------------------------------------------
    def reset_state(self) -> None:
        """重置一局游戏（蛇、得分、关卡计时等）。"""
        cx, cy = GRID_W // 2, GRID_H // 2
        self.snake: deque[tuple[int, int]] = deque(
            [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        )
        self.direction: tuple[int, int] = (1, 0)
        self.next_direction: tuple[int, int] = (1, 0)
        self.food: tuple[int, int] = self._spawn_food()
        self.score = 0
        self.alive = True
        self.paused = False
        self.game_over = False
        self.delay_ms = INITIAL_DELAY_MS
        self.food_eaten = 0
        self.level = 1
        self.level_target = LEVEL_BASE_TARGET
        self.obstacles: set[tuple[int, int]] = self._generate_obstacles(1)
        self.special: tuple[int, int] | None = None
        self.special_kind: str | None = None  # 'gold' / 'hot'
        self.hot_until_ms: int = 0  # 绝对时间戳，毫秒
        # 若新生成的食物落在了障碍上，重新选位置
        while self.food in self.obstacles:
            self.food = self._spawn_food()

    def _spawn_food(self) -> tuple[int, int]:
        """在不与蛇身/障碍重叠的格子中随机生成一个食物。"""
        snake_set = set(self.snake)
        free = [
            (x, y)
            for x in range(GRID_W)
            for y in range(GRID_H)
            if (x, y) not in snake_set and (x, y) not in self.obstacles
        ]
        # free 永远非空，因为网格远大于起手蛇长
        return random.choice(free)

    def _level_obstacle_count(self, level: int) -> int:
        """关卡等级对应的障碍数量。"""
        return LEVEL_BASE_OBSTACLES + (level - 1) * LEVEL_OBSTACLE_STEP

    def _level_target_len(self, level: int) -> int:
        """关卡等级对应的通关蛇长。"""
        return LEVEL_BASE_TARGET + (level - 1) * LEVEL_TARGET_STEP

    def _generate_obstacles(self, level: int) -> set[tuple[int, int]]:
        """为指定关卡生成一组障碍。避开初始蛇身与地图边界一格。"""
        count = self._level_obstacle_count(level)
        snake_set = set(self.snake)
        # 候选格：避开蛇身、避开地图最外圈（让玩家有一圈缓冲）
        candidates = [
            (x, y)
            for x in range(1, GRID_W - 1)
            for y in range(1, GRID_H - 1)
            if (x, y) not in snake_set
        ]
        # 限制最大可放数量，避免关卡无限叠加导致无空间
        # 用候选池的 1/3 作为密度上限
        max_count = min(count, max(1, len(candidates) // 3))
        chosen: set[tuple[int, int]] = set()
        attempts = 0
        while len(chosen) < max_count and attempts < max_count * 6:
            attempts += 1
            p = random.choice(candidates)
            # 拒绝紧邻初始蛇头，给玩家起步空间
            hx, hy = self.snake[0]
            if abs(p[0] - hx) + abs(p[1] - hy) < 3:
                continue
            chosen.add(p)
        return chosen

    def _next_level(self) -> None:
        """进入下一关：障碍重置，关号 +1，目标增长，蛇身保留。"""
        self.level += 1
        self.level_target = self._level_target_len(self.level)
        self.obstacles = self._generate_obstacles(self.level)
        # 清空特殊食物（避免卡在新障碍上）
        self.special = None
        self.special_kind = None
        # 确保当前食物和蛇头位置合法
        if self.food in self.obstacles:
            self.food = self._spawn_food()
        # 略微提速但保留最低下限
        self.delay_ms = max(MIN_DELAY_MS, self.delay_ms - SPEEDUP_STEP_MS)

    def _maybe_drop_special(self) -> None:
        """每帧按概率在空闲格生成一个特殊食物。"""
        if self.special is not None:
            return
        if random.random() > SPECIAL_SPAWN_CHANCE:
            return
        snake_set = set(self.snake)
        free = [
            (x, y)
            for x in range(1, GRID_W - 1)
            for y in range(1, GRID_H - 1)
            if (x, y) not in snake_set
            and (x, y) not in self.obstacles
            and (x, y) != self.food
        ]
        if not free:
            return
        kind = random.choice(("gold", "hot"))
        self.special = random.choice(free)
        self.special_kind = kind

    def _apply_special(self, kind: str) -> None:
        """吃到特殊食物后的效果（金豆 / 辣豆）。"""
        now_ms = self._now_ms()
        if kind == "gold":
            self.score += GOLD_SCORE
            # 缩短蛇身（最少保留 2 节，避免长度不足一节带来的边界处理）
            target_len = max(2, len(self.snake) - GOLD_SHORTEN)
            while len(self.snake) > target_len:
                self.snake.pop()
        elif kind == "hot":
            self.score += HOT_SCORE
            self.hot_until_ms = now_ms + HOT_DURATION_MS
        self.special = None
        self.special_kind = None

    @staticmethod
    def _now_ms() -> int:
        # tkinter 没有高分辨率计时 API，time.time() 完全够用
        import time
        return int(time.time() * 1000)

    # ----------------------------------------------------------------------
    # 主循环
    # ----------------------------------------------------------------------
    def tick(self) -> None:
        """每帧推进游戏状态，然后重绘并调度下一帧。"""
        if not self.paused and self.alive:
            self._step()

        # 食物脉冲动画
        self._food_pulse = (self._food_pulse + 0.18) % (2 * 3.1415926)

        self.draw()

        if self._frame_id is not None:
            try:
                self.root.after_cancel(self._frame_id)
            except tk.TclError:
                pass
        self._frame_id = self.root.after(self.delay_ms, self.tick)

    def _step(self) -> None:
        """推进一格，处理碰撞与得分。"""
        # 应用玩家输入的方向（不允许 180° 反向）
        self.direction = self.next_direction
        dx, dy = self.direction
        hx, hy = self.snake[0]
        new_head = (hx + dx, hy + dy)

        # 撞墙
        if not (0 <= new_head[0] < GRID_W and 0 <= new_head[1] < GRID_H):
            self._die()
            return

        # 撞障碍
        if new_head in self.obstacles:
            self._die()
            return

        # 撞自己（注意：移动时蛇尾将移开，因此尾部位置可视为安全）
        tail = self.snake[-1]
        body = set(self.snake)
        body.discard(tail)
        if new_head in body:
            self._die()
            return

        self.snake.appendleft(new_head)

        # 先看是否吃到特殊食物（优先级最高）
        if (
            self.special is not None
            and self.special_kind is not None
            and new_head == self.special
        ):
            self._apply_special(self.special_kind)
            # 金豆不增长蛇身，所以这里不要 pop；辣豆也不增长
            self._maybe_speedup()
            self._maybe_drop_special()
            return

        if new_head == self.food:
            self.score += FOOD_SCORE
            self.food_eaten += 1
            self._maybe_speedup()
            self.food = self._spawn_food()
            self._maybe_drop_special()
            # 通关判定：吃普通食物后蛇长达到目标
            if len(self.snake) >= self.level_target:
                self._next_level()
        else:
            self.snake.pop()
            # 即使没吃到，也按概率随机出特殊食物
            self._maybe_drop_special()

    def _maybe_speedup(self) -> None:
        if self.food_eaten > 0 and self.food_eaten % SPEEDUP_EVERY == 0:
            self.delay_ms = max(
                MIN_DELAY_MS, self.delay_ms - SPEEDUP_STEP_MS
            )

    def _die(self) -> None:
        self.alive = False
        self.game_over = True
        if self.score > self.high_score:
            self.high_score = self.score

    # ----------------------------------------------------------------------
    # 输入
    # ----------------------------------------------------------------------
    def on_key(self, event: tk.Event) -> None:
        """全局按键回调。"""
        key = event.keysym
        if key in DIRECTION_KEYS:
            if not self.alive or self.paused:
                return
            new_dir = DIRECTION_KEYS[key]
            # 辣豆状态下：左右键 / 上下键交叉互换
            #   按 ←/→ 实际转为 ↑/↓ ；按 ↑/↓ 实际转为 ←/→
            #   实现：方向向量 (dx, dy) → (dy, dx)
            if self._now_ms() < self.hot_until_ms:
                dx, dy = new_dir
                if dx != 0 or dy != 0:
                    new_dir = (dy, dx)
            # 禁止 180° 反向（基于当前实际蛇向）
            if new_dir == (-self.direction[0], -self.direction[1]):
                return
            self.next_direction = new_dir
            return

        low = key.lower()
        if low == "p":
            if self.game_over:
                return
            self.paused = not self.paused
        elif low == "r":
            # 任意时刻按 R 重开
            self.reset_state()
        elif low == "escape":
            self.quit_game()

    def quit_game(self) -> None:
        if self._frame_id is not None:
            try:
                self.root.after_cancel(self._frame_id)
            except tk.TclError:
                pass
        self.root.destroy()

    # ----------------------------------------------------------------------
    # 渲染
    # ----------------------------------------------------------------------
    def draw(self) -> None:
        """整帧重绘：状态栏 + 网格 + 障碍 + 蛇 + 食物 + 特殊食物 + 覆盖层。"""
        c = self.canvas
        c.delete("all")
        self._draw_grid(c)
        self._draw_obstacles(c)
        self._draw_food(c)
        self._draw_special(c)
        self._draw_snake(c)
        self._draw_header(c)
        if self.paused and not self.game_over:
            self._draw_center_text(c, "PAUSED", "按 P 继续")
        elif self.game_over:
            msg = "GAME OVER"
            sub = "按 R 重开 · ESC 退出"
            self._draw_center_text(c, msg, sub)

    def _draw_grid(self, c: tk.Canvas) -> None:
        x0, y0 = 0, HEADER_H
        x1, y1 = GRID_W * CELL, HEADER_H + GRID_H * CELL
        # 棋盘背景
        c.create_rectangle(x0, y0, x1, y1, fill=BG_COLOR, outline="")
        # 网格线
        for i in range(GRID_W + 1):
            c.create_line(
                i * CELL, y0, i * CELL, y1, fill=GRID_COLOR, width=1
            )
        for j in range(GRID_H + 1):
            c.create_line(
                x0, y0 + j * CELL, x1, y0 + j * CELL, fill=GRID_COLOR, width=1
            )

    def _draw_food(self, c: tk.Canvas) -> None:
        x, y = self.food
        # 呼吸缩放：脉冲值映射为 0.78 ~ 1.0
        scale = 0.88 + 0.12 * (0.5 + 0.5 * math.sin(self._food_pulse))
        size = CELL * scale
        pad = (CELL - size) / 2
        cx = x * CELL + CELL / 2
        cy = HEADER_H + y * CELL + CELL / 2
        # 食物阴影
        c.create_oval(
            cx - size / 2 + 1,
            cy - size / 2 + 2,
            cx + size / 2 + 1,
            cy + size / 2 + 2,
            fill="",
            outline="",
            stipple="gray25",
        )
        # 食物本体
        c.create_oval(
            cx - size / 2,
            cy - size / 2,
            cx + size / 2,
            cy + size / 2,
            fill=FOOD_COLOR_A,
            outline="",
        )
        # 高光
        hl = size * 0.35
        c.create_oval(
            cx - size * 0.28,
            cy - size * 0.32,
            cx - size * 0.28 + hl,
            cy - size * 0.32 + hl,
            fill=FOOD_COLOR_B,
            outline="",
        )

    def _draw_special(self, c: tk.Canvas) -> None:
        """绘制特殊食物（金豆 / 辣豆）。"""
        if self.special is None or self.special_kind is None:
            return
        x, y = self.special
        # 比普通食物略大一点，更醒目
        scale = 0.95 + 0.05 * (0.5 + 0.5 * math.sin(self._food_pulse * 1.5))
        size = CELL * scale
        cx = x * CELL + CELL / 2
        cy = HEADER_H + y * CELL + CELL / 2
        if self.special_kind == "gold":
            color_main, color_hi = GOLD_COLOR_A, GOLD_COLOR_B
        else:  # hot
            color_main, color_hi = HOT_COLOR_A, HOT_COLOR_B
        # 外发光（用一个略大的同色圆 + stipple 模拟）
        c.create_oval(
            cx - size * 0.7,
            cy - size * 0.7,
            cx + size * 0.7,
            cy + size * 0.7,
            fill=color_main,
            outline="",
            stipple="gray25",
        )
        # 本体
        c.create_oval(
            cx - size / 2,
            cy - size / 2,
            cx + size / 2,
            cy + size / 2,
            fill=color_main,
            outline="",
        )
        # 高光
        c.create_oval(
            cx - size * 0.28,
            cy - size * 0.32,
            cx - size * 0.28 + size * 0.35,
            cy - size * 0.32 + size * 0.35,
            fill=color_hi,
            outline="",
        )
        # 标识字母
        letter = "G" if self.special_kind == "gold" else "H"
        c.create_text(
            cx,
            cy,
            text=letter,
            fill="#0d1422",
            font=self.small_font,
        )

    def _draw_obstacles(self, c: tk.Canvas) -> None:
        """绘制当前关卡的障碍。"""
        if not self.obstacles:
            return
        for (gx, gy) in self.obstacles:
            x0 = gx * CELL + 1
            y0 = HEADER_H + gy * CELL + 1
            x1 = (gx + 1) * CELL - 1
            y1 = HEADER_H + (gy + 1) * CELL - 1
            # 主体（圆角效果用四圆 + 中矩形）
            c.create_rectangle(
                x0 + 2, y0 + 2, x1 - 2, y1 - 2,
                fill=OBSTACLE_COLOR, outline="",
            )
            d = 4
            for cx, cy in (
                (x0, y0), (x1, y0), (x0, y1), (x1, y1),
            ):
                c.create_oval(cx - d, cy - d, cx + d, cy + d, fill=OBSTACLE_COLOR, outline="")
            # 顶部高光
            c.create_rectangle(
                x0 + 3, y0 + 3, x1 - 3, y0 + 5,
                fill="#7d8aa3", outline="",
            )

    def _draw_snake(self, c: tk.Canvas) -> None:
        body = list(self.snake)
        n = len(body)
        # 身：从尾部到头部颜色由暗到亮；头单独画
        for i in range(n - 1, 0, -1):
            x, y = body[i]
            t = i / max(1, n - 1)  # 0 (尾) ~ 1 (接近头)
            color = self._lerp_color(SNAKE_BODY_DARK, SNAKE_BODY_LIGHT, t)
            self._draw_cell(c, x, y, color, radius=5)
        # 头
        hx, hy = body[0]
        self._draw_cell(c, hx, hy, SNAKE_HEAD, radius=6)
        # 眼睛（朝向 direction）
        dx, dy = self.direction
        eye_offsets = self._eye_offsets(dx, dy)
        for ox, oy in eye_offsets:
            ex = hx * CELL + ox
            ey = HEADER_H + hy * CELL + oy
            c.create_oval(ex - 2, ey - 2, ex + 2, ey + 2, fill=BG_COLOR, outline="")

    def _eye_offsets(self, dx: int, dy: int) -> list[tuple[int, int]]:
        """根据朝向返回两个眼睛在格子内的像素偏移。"""
        cx = CELL / 2
        cy = CELL / 2
        # 离格中心稍偏前
        forward_x = cx + dx * (CELL * 0.18)
        forward_y = cy + dy * (CELL * 0.18)
        # 两侧偏移
        side_a = (dy, -dx)
        side_b = (-dy, dx)
        return [
            (
                forward_x + side_a[0] * (CELL * 0.22),
                forward_y + side_a[1] * (CELL * 0.22),
            ),
            (
                forward_x + side_b[0] * (CELL * 0.22),
                forward_y + side_b[1] * (CELL * 0.22),
            ),
        ]

    def _draw_cell(
        self,
        c: tk.Canvas,
        gx: int,
        gy: int,
        color: str,
        radius: int = 5,
    ) -> None:
        x0 = gx * CELL + 2
        y0 = HEADER_H + gy * CELL + 2
        x1 = (gx + 1) * CELL - 2
        y1 = HEADER_H + (gy + 1) * CELL - 2
        c.create_rectangle(
            x0, y0, x1, y1, fill=color, outline="", width=0
        )
        # 圆角效果：用同色再叠四个小圆
        d = radius
        for cx, cy in (
            (x0, y0), (x1, y0), (x0, y1), (x1, y1),
        ):
            c.create_oval(cx - d, cy - d, cx + d, cy + d, fill=color, outline="")

    def _draw_header(self, c: tk.Canvas) -> None:
        c.create_rectangle(
            0, 0, GRID_W * CELL, HEADER_H, fill=HEADER_COLOR, outline=""
        )
        # 分隔线
        c.create_line(
            0, HEADER_H, GRID_W * CELL, HEADER_H, fill=GRID_COLOR, width=1
        )
        # 标题
        c.create_text(
            INFO_W,
            HEADER_H / 2,
            text="SNAKE",
            font=self.title_font,
            fill=ACCENT_COLOR,
            anchor="w",
        )
        c.create_text(
            INFO_W + 70,
            HEADER_H / 2,
            text=f"v{__version__}",
            font=self.small_font,
            fill=SUBTLE_COLOR,
            anchor="w",
        )
        # 关卡
        c.create_text(
            INFO_W + 130,
            HEADER_H / 2,
            text=f"LV {self.level:02d}",
            font=self.title_font,
            fill=FOOD_COLOR_B,
            anchor="w",
        )
        # 关卡目标
        target = self.level_target
        c.create_text(
            INFO_W + 130,
            HEADER_H / 2 + 13,
            text=f"目标 ≥ {target:02d}",
            font=self.small_font,
            fill=SUBTLE_COLOR,
            anchor="w",
        )

        # 反转（辣豆）状态提示
        if self._now_ms() < self.hot_until_ms:
            remain = max(0, (self.hot_until_ms - self._now_ms()) / 1000)
            c.create_text(
                GRID_W * CELL // 2,
                HEADER_H / 2,
                text=f"⚡ 反转 {remain:.1f}s",
                font=self.title_font,
                fill=INVERT_TINT,
                anchor="w",
            )

        # 右侧统计
        score_text = f"SCORE {self.score:04d}"
        c.create_text(
            GRID_W * CELL - INFO_W,
            HEADER_H / 2 - 9,
            text=score_text,
            font=self.title_font,
            fill=TEXT_COLOR,
            anchor="e",
        )
        sub = (
            f"BEST {self.high_score:04d}   "
            f"LEN {len(self.snake):02d}   "
            f"{'PAUSED' if self.paused else ('OVER' if self.game_over else 'PLAYING')}"
        )
        c.create_text(
            GRID_W * CELL - INFO_W,
            HEADER_H / 2 + 12,
            text=sub,
            font=self.small_font,
            fill=(
                DANGER_COLOR
                if self.game_over
                else (SUBTLE_COLOR if not self.paused else ACCENT_COLOR)
            ),
            anchor="e",
        )

    def _draw_center_text(self, c: tk.Canvas, title: str, sub: str) -> None:
        cx = GRID_W * CELL / 2
        cy = HEADER_H + GRID_H * CELL / 2
        # 半透明遮罩
        c.create_rectangle(
            0, HEADER_H, GRID_W * CELL, HEADER_H + GRID_H * CELL,
            fill="#000000", stipple="gray50", outline="",
        )
        big = tkfont.Font(family="Menlo", size=28, weight="bold")
        c.create_text(
            cx, cy - 14, text=title, font=big,
            fill=ACCENT_COLOR if title == "PAUSED" else DANGER_COLOR,
        )
        c.create_text(
            cx, cy + 22, text=sub, font=self.small_font, fill=TEXT_COLOR,
        )

    # ----------------------------------------------------------------------
    @staticmethod
    def _lerp_color(a: str, b: str, t: float) -> str:
        """RGB 颜色线性插值。t=0 返回 a，t=1 返回 b。"""
        ah = a.lstrip("#")
        bh = b.lstrip("#")
        ra, ga, ba = int(ah[0:2], 16), int(ah[2:4], 16), int(ah[4:6], 16)
        rb, gb, bb = int(bh[0:2], 16), int(bh[2:4], 16), int(bh[4:6], 16)
        r = int(ra + (rb - ra) * t)
        g = int(ga + (gb - ga) * t)
        bl = int(ba + (bb - ba) * t)
        return f"#{r:02x}{g:02x}{bl:02x}"


# ============================================================================
# 入口
# ============================================================================
def main() -> int:
    root = tk.Tk()
    try:
        SnakeGame(root)
    except tk.TclError as e:
        # macOS / 无图形界面时 tkinter 可能初始化失败
        print(f"无法初始化窗口：{e}", file=sys.stderr)
        print("请确认你的环境支持图形界面（macOS / Windows / Linux 桌面）。", file=sys.stderr)
        return 1
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
