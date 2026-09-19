# Snake 🐍 — v0.10.21

经典贪吃蛇小游戏，**单文件** Python 实现，**零第三方依赖**（仅使用标准库 `tkinter`）。  
支持键盘控制、暂停、重开、得分统计与平滑提速，附带食物脉冲动画与蛇身渐变颜色。

![Snake demo](https://img.shields.io/badge/version-0.10.21-brightgreen) ![python](https://img.shields.io/badge/python-3.8%2B-blue) ![deps](https://img.shields.io/badge/dependencies-zero-success)

---

## ✨ 特性

- **单文件运行**：`snake_game.py` 即可，跨 macOS / Windows / Linux 桌面。
- **零外部依赖**：仅依赖 Python 自带的 `tkinter`。
- **流畅体验**：基于 `tkinter.after` 的稳定帧循环，每 5 个食物提速一次。
- **键盘友好**：支持方向键与 WASD 双键位，控制不冲突。
- **得分机制**：每颗食物 +10 分，状态栏显示本局分数 / 历史最高 / 蛇长。
- **可视化细节**：蛇身渐变、头部朝向眼睛、食物呼吸缩放、撞墙/撞自己即死、GAME OVER 覆盖层。

---

## 🎮 游戏目标

用方向键（或 `WASD`）控制蛇在网格中移动，**吃掉尽可能多的食物**，每颗食物 +10 分。
撞墙或撞自己即结束本局 —— 经典规则，简单直接。

---

## ⌨️ 操作说明

| 按键 | 作用 |
|------|------|
| `↑ ↓ ← →` 或 `W A S D` | 控制蛇移动方向 |
| `P` | 暂停 / 继续 |
| `R` | 任意时刻重开新一局 |
| `ESC` | 退出游戏 |

> **小贴士**：蛇不能 180° 反向调头。如果你在快速按方向键时发现蛇「卡住」，那是规则在阻止你自我碰撞。

---

## 🚀 运行

需要 Python 3.8+（tkinter 在标准安装中默认包含）。

```bash
# 方式一
python3 snake_game.py

# 方式二
chmod +x snake_game.py
./snake_game.py
```

> 在 macOS / Windows 的标准 Python 安装中可直接运行。  
> 在 headless Linux 服务器（如无 X11 / 无图形栈），tkinter 无法创建窗口，请改在本机或有桌面的环境运行。

---

## 🧩 自定义

所有可调参数都集中在 `snake_game.py` 文件顶部的「常量」区，常见可调项：

| 常量 | 默认 | 含义 |
|------|------|------|
| `GRID_W`, `GRID_H` | 26, 22 | 网格宽高（格子数） |
| `CELL` | 22 | 单格像素 |
| `INITIAL_DELAY_MS` | 110 | 起手帧间隔（毫秒），越小越快 |
| `MIN_DELAY_MS` | 45 | 速度上限 |
| `SPEEDUP_EVERY` | 5 | 每吃 N 颗食物提速一次 |
| `FOOD_SCORE` | 10 | 每颗食物得分 |

修改后保存即可热运行（重新执行 `python3 snake_game.py`）。

---

## 🗂️ 项目结构

```
snake-game/
├── snake_game.py        # 主程序（单文件）
├── README.md            # 本文件
├── LICENSE              # MIT 许可证
└── requirements.txt     # 显式声明无第三方依赖（仅留作说明）
```

---

## 📜 许可

本项目以 **MIT 协议** 发布，详见 [LICENSE](./LICENSE)。

---

## 🧾 版本

- **0.10.21** — 初版发布：经典玩法 + 渐变配色 + 食物呼吸 + 暂停/重开 + 键盘双键位
