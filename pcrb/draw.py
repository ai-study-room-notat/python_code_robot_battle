import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME

###############################################################################
# ユーティリティ関数
###############################################################################

def safe_load_image(path: str):
    """画像ファイルを読み込みます。

    ファイルが存在しない、または読み込みに失敗した場合は ``None`` を返します。
    呼び出し側ではこの ``None`` を検知して散布図用マーカーへフォールバック描画できます。"""
    if os.path.exists(path):
        try:
            return plt.imread(path)
        except Exception:
            pass
    return None


def add_image_to_plot(
    ax: plt.Axes,
    img,
    x: int,
    y: int,
    *,
    zoom: float = 1.0,
    fallback_color: str = "white",
    marker: str = "s",
):
    """ボード座標 ``(x, y)`` へ ``img`` を描画します。

    ``img`` が ``None`` の場合は色付きスクエアを代わりに表示し、
    スプライトが欠けているときでもアクションの手応えを失わないようにします。"""

    if img is not None:
        imagebox = OffsetImage(img, zoom=zoom)
        ab = AnnotationBbox(imagebox, (x, y), frameon=False)
        ax.add_artist(ab)
    else:
        ax.scatter(x, y, color=fallback_color, s=100, marker=marker, edgecolors="black")

###############################################################################
# 共通ヘルパ
###############################################################################

def _direction_offset(direction: str) -> Tuple[int, int]:
    """移動／罠の方向を (dx, dy) で返します。"""
    mapping = {
        "right": (-1, 0),  # ボード座標は x+→、matplotlib は origin="upper" なので y 軸は反転
        "left": (1, 0),
        "down": (0, -1),
        "up": (0, 1),
        "trap_right": (-1, 0),
        "trap_left": (1, 0),
        "trap_down": (0, -1),
        "trap_up": (0, 1),
    }
    return mapping[direction]


def _collect_robot_positions(turn_data: dict) -> Dict[str, Tuple[int, int]]:
    """ターン情報から各ロボットの座標を抽出して返す。"""
    return {r["name"]: tuple(r["position"]) for r in turn_data["robots"]}


def _collect_action_targets(
    turn_data: dict,
    x_max: int,
    y_max: int,
    robot_positions: Dict[str, Tuple[int, int]],
) -> Dict[str, List[Tuple[int, int]]]:
    """行動タイプごとにハイライト対象マスを計算して返す。"""

    targets: Dict[str, List[Tuple[int, int]]] = defaultdict(list)

    player = turn_data["action"]["robot_name"]
    if player is None:
        return targets

    rx, ry = robot_positions[player]
    action = turn_data["action"]["action"]

    in_field = lambda x, y: 0 <= x < x_max and 0 <= y < y_max

    if action == "attack":
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = rx + dx, ry + dy
            if in_field(nx, ny):
                targets["attack"].append((ny, nx))

    elif action == "rest":
        targets["rest"].append((ry, rx))

    elif action in {"right", "left", "down", "up"}:
        dx, dy = _direction_offset(action)
        nx, ny = rx + dx, ry + dy
        if in_field(nx, ny):
            targets["move"].append((ny, nx))

    elif action == "defend":
        targets["defend"].append((ry, rx))

    elif action == "parry":
        targets["parry"].append((ry, rx))

    elif action == "ranged_attack":
        for dx, dy in [
            (-2, 0), (2, 0), (0, -2), (0, 2),
            (1, 1), (-1, -1), (1, -1), (-1, 1),
        ]:
            nx, ny = rx + dx, ry + dy
            if in_field(nx, ny):
                targets["ranged_attack"].append((ny, nx))

    elif action.startswith("trap_"):
        dx, dy = _direction_offset(action)
        nx, ny = rx + dx, ry + dy
        if in_field(nx, ny):
            targets["trap"].append((ny, nx))

    elif action == "steal":
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = rx + dx, ry + dy
            if in_field(nx, ny):
                targets["steal"].append((ny, nx))

    elif action == "teleport":
        targets["teleport"].append((ry, rx))

    elif action == "camouflage":
        targets["camouflage"].append((ry, rx))

    elif action == "scan":
        targets["scan"].append((ry, rx))

    return targets

###############################################################################
# 散布図ベースのボード (v1)
###############################################################################

def draw_board(turn_data: dict, x_max: int, y_max: int, *, red_robot_name: str, blue_robot_name: str, title: str = "", is_show: bool = True):
    """散布図を用いたシンプルな可視化関数。"""

    # 共通情報生成
    robot_positions = _collect_robot_positions(turn_data)
    markers = _collect_action_targets(turn_data, x_max, y_max, robot_positions)

    # ボード初期化: 0 = 空, 1 = 赤ロボット, 2 = 青ロボット
    board = np.zeros((y_max, x_max))
    for name, (x, y) in robot_positions.items():
        board[y, x] = 1 if name == red_robot_name else 2

    # Figure
    plt.figure(figsize=(6, 6))
    cmap = plt.colormaps.get_cmap("coolwarm").resampled(3)
    plt.imshow(board, cmap=cmap, origin="upper")
    plt.clim(0, 2)
    plt.xticks(np.arange(0, x_max, 1))
    plt.yticks(np.arange(0, y_max, 1))
    plt.grid(color="gray", linestyle="-", linewidth=0.5)

    # アクション→色
    colour_map = {
        "attack": "red",
        "rest": "green",
        "move": "black",
        "defend": "yellow",
        "parry": "cyan",
        "ranged_attack": "orange",
        "trap": "purple",
        "steal": "magenta",
        "teleport": "brown",
        "camouflage": "grey",
        "scan": "blue",
    }

    for key, positions in markers.items():
        for y, x in positions:
            plt.scatter(x, y, color=colour_map[key], s=100, marker="s", edgecolors="black")

    if title:
        plt.title(title)
    if is_show:
        plt.show()
    return plt

###############################################################################
# スプライトベースのボード (v2)
###############################################################################

def draw_board_v2(
    turn_data: dict,
    x_max: int,
    y_max: int,
    *,
    red_robot_name: str,
    blue_robot_name: str,
    title: str = "",
    is_show: bool = True,
):
    """スプライトを用いたリッチな可視化関数。"""

    # 共通情報生成
    robot_positions = _collect_robot_positions(turn_data)
    markers = _collect_action_targets(turn_data, x_max, y_max, robot_positions)

    # ----------------------------------------------------------------------
    # スプライト読み込み
    # ----------------------------------------------------------------------
    asset_dir = "./pcrb/asset"
    sprites = {
        "tile": safe_load_image(os.path.join(asset_dir, "tile.png")),
        "robot_a": safe_load_image(os.path.join(asset_dir, "red_robot.png")),
        "robot_b": safe_load_image(os.path.join(asset_dir, "blue_robot.png")),
        "attack": safe_load_image(os.path.join(asset_dir, "attack.png")),
        "rest": safe_load_image(os.path.join(asset_dir, "rest.png")),
        "move": safe_load_image(os.path.join(asset_dir, "move.png")),
        "defend": safe_load_image(os.path.join(asset_dir, "defend.png")),
        "parry": safe_load_image(os.path.join(asset_dir, "parry.png")),
        "ranged_attack": safe_load_image(os.path.join(asset_dir, "ranged_attack.png")),
        "trap": safe_load_image(os.path.join(asset_dir, "trap.png")),
        "steal": safe_load_image(os.path.join(asset_dir, "steal.png")),
        "teleport": safe_load_image(os.path.join(asset_dir, "teleport.png")),
        "camouflage": safe_load_image(os.path.join(asset_dir, "camouflage.png")),
        "scan": safe_load_image(os.path.join(asset_dir, "scan.png")),
    }

    # ----------------------------------------------------------------------
    # Figure / Axes 準備
    # ----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.tick_params(colors="white")
    ax.set_xlim(-0.5, x_max - 0.5)
    ax.set_ylim(-0.5, y_max - 0.5)
    ax.set_xticks(np.arange(0, x_max, 1))
    ax.set_yticks(np.arange(0, y_max, 1))
    ax.grid(color="gray", linestyle="-", linewidth=0.5)
    ax.set_aspect("equal")

    # 背景タイル
    for x in range(x_max):
        for y in range(y_max):
            add_image_to_plot(ax, sprites["tile"], x, y, zoom=1.0, fallback_color="#444")

    # ----------------------------------------------------------------------
    # ロボット描画
    # ----------------------------------------------------------------------
    for name, (x, y) in robot_positions.items():
        if name == red_robot_name:
            sprite = sprites["robot_a"]
            fallback = "white"
        else:
            sprite = sprites["robot_b"]
            fallback = "lightblue"
        add_image_to_plot(ax, sprite, x, y, zoom=0.9, fallback_color=fallback)

    # ----------------------------------------------------------------------
    # アクションハイライト描画
    # ----------------------------------------------------------------------
    colour_fallback = {
        "attack": "red",
        "rest": "green",
        "move": "black",
        "defend": "yellow",
        "parry": "cyan",
        "ranged_attack": "orange",
        "trap": "purple",
        "steal": "magenta",
        "teleport": "brown",
        "camouflage": "grey",
        "scan": "blue",
    }

    for key, positions in markers.items():
        sprite = sprites.get(key)
        for y, x in positions:
            add_image_to_plot(ax, sprite, x, y, zoom=0.9, fallback_color=colour_fallback[key])

    # ----------------------------------------------------------------------
    # タイトル／表示
    # ----------------------------------------------------------------------
    if title:
        ax.set_title(title, color="white")
    if is_show:
        plt.show()

    return fig
