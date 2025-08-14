import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import ast
import traceback
import json

from pcrb.controller import GameController
from pcrb.robot import Robot
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME

# 許可する関数とモジュール
ALLOWED_FUNCTIONS = {"robot_logic"}
ALLOWED_MODULES = ["random", "math"]
GAME_STATE_FILE = "./game_state.json"  # 既存の game_state.json ファイル


# ----------------------------- セキュリティ関連ユーティリティ -----------------------------

def is_safe_code(file_content: str) -> tuple[bool, str]:
    """アップロードされたコードを AST 解析し、安全性を判定する。"""
    try:
        tree = ast.parse(file_content)

        for node in ast.walk(tree):
            # インポートのチェック
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in ALLOWED_MODULES:
                        return False, f"許可されていないモジュールのインポート: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module not in ALLOWED_MODULES:
                    return False, f"許可されていないモジュールのインポート: {node.module}"

            # 許可していない関数定義を禁止
            if isinstance(node, ast.FunctionDef):
                if node.name not in ALLOWED_FUNCTIONS:
                    return False, f"許可されていない関数定義: {node.name}"

            # 危険な関数呼び出しの検出
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval"}:
                    return False, f"禁止されている関数呼び出し: {node.func.id}"

        return True, "安全なコードです"
    except Exception as e:
        error_details = traceback.format_exc()
        print(error_details)
        return False, f"コード解析中にエラーが発生しました: {e}"


# ----------------------------- モジュールロード -----------------------------

def load_player_module(file_content: str):
    """サンドボックス環境でアップロードされたモジュールをロードする。"""
    import importlib.util
    import textwrap

    file_path = "./uploaded_logic_safe.py"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(file_content))

    spec = importlib.util.spec_from_file_location("robot_logic_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return getattr(module, "robot_logic", None)


# ----------------------------- ゲーム実行 -----------------------------

def play_game(robot1_logic, robot2_logic, robot1_name=PLAYER_ROBOT_NAME, robot2_name=ENEMY_ROBOT_NAME):
    controller = GameController(max_turn=100, x_max=9, y_max=7)
    robot1 = Robot(robot1_name, 1, 3, robot1_logic, controller)
    robot2 = Robot(robot2_name, 7, 3, robot2_logic, controller)
    controller.set_robots(robot1, robot2)
    winner, game_state = controller.game_loop()
    return winner, game_state


def game_state_download_button(game_state: dict) -> None:
    """game_state を JSON としてダウンロード可能にするボタンを描画。"""
    json_bytes = json.dumps(game_state, ensure_ascii=False, indent=4).encode("utf-8")
    st.download_button(
        label="game_state.json をダウンロード",
        data=json_bytes,
        file_name="game_state.json",
        mime="application/json",
    )


def main():
    from pages.main import main as main_page
    from pages.drawer import main as drawer_page
    from pages.manuel import main as manuel_page
    from pages.robot_battle_page import main as robot_battle_page
    from pages.robot_logic_editor import main as robot_logic_editor_page
    from pages.tutorial import main as tutorial_page
    from pages.local_battle_page import main as local_battle_page # Add local_battle_page

    page = st.navigation({
        "Main": [
            st.Page(main_page, title="Home", icon="🏠", url_path="", default=True),
            st.Page(tutorial_page, title="Tutorial", icon="📚", url_path="tutorial_page"),
            st.Page(manuel_page, title="Manual", icon="📖", url_path="manuel"),
            st.Page(drawer_page, title="Drawer", icon="🖌️", url_path="drawer"),
            st.Page(robot_battle_page, title="Robot Battle", icon="🤖", url_path="robot_battle_page"),
            st.Page(local_battle_page, title="Local Battle", icon="🆚", url_path="local_battle_page"), # Add local_battle_page to navigation
            st.Page(robot_logic_editor_page, title="Logic Editor", icon="🛠️", url_path="robot_logic_editor"),
        ]
    }).run()


if __name__ == "__main__":
    main()
