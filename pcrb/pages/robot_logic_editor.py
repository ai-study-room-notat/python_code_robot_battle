import streamlit as st
import textwrap
import os
import traceback

from controller import GameController
from robot import Robot
from draw import draw_board_v2 as draw_board
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME

def main():

    st.set_page_config(layout="wide")

    # ------------------------------------------------------------------------
    # 初期 robot_logic コード
    # ------------------------------------------------------------------------
    default_code = textwrap.dedent("""
    def robot_logic(robot, game_info, memos):
        # Example logic
        enemy_position = game_info['enemy_position']
        enemy_hp = game_info['enemy_hp']
        distance = abs(robot.position[0] - enemy_position[0]) + abs(robot.position[1] - enemy_position[1])
        memo = {'enemy_position': str(enemy_position)}

        if robot.sp < 20:
            return "rest", memo

        if distance == 1:
            return "attack", memo

        if distance == 2 and robot.sp >= 15:
            return "ranged_attack", memo

        if robot.position[0] < enemy_position[0]:
            return "right", memo
        elif robot.position[0] > enemy_position[0]:
            return "left", memo
        elif robot.position[1] < enemy_position[1]:
            return "down", memo
        else:
            return "up", memo
    """)

    # ------------------------------------------------------------------------
    # セッションステート初期化
    # ------------------------------------------------------------------------
    session_defaults = {
        "robot_code":           default_code,
        "last_opponent_action": None,
        "show_initial_state":   True,
    }

    for k, v in session_defaults.items():
        st.session_state.setdefault(k, v)

    # ------------------------------------------------------------------------
    # GameController とロボットをセッションに保持
    # ------------------------------------------------------------------------
    if "controller" not in st.session_state:
        controller = GameController()
        player     = Robot(PLAYER_ROBOT_NAME,   1, 3, None, controller)
        enemy      = Robot(ENEMY_ROBOT_NAME, 7, 3, None, controller)
        controller.set_robots(player, enemy)

        st.session_state["controller"]     = controller
        st.session_state["player_robot"]   = player
        st.session_state["opponent_robot"] = enemy
    else:
        controller   = st.session_state["controller"]
        player       = st.session_state["player_robot"]
        enemy        = st.session_state["opponent_robot"]

    # ------------------------------------------------------------------------
    # 画面レイアウト
    # ------------------------------------------------------------------------
    st.title("Robot Logic Editor")

    # 現在のゲームの状況を描画
    if controller.game_state:
        settings = controller.game_state[0]['settings']
        x_max = settings['x_max']
        y_max = settings['y_max']

        current_turn_data = controller.game_state[-1]
        if "robots" in current_turn_data:
            fig_placeholder = st.empty()  # プレースホルダーを作成
            fig = draw_board(current_turn_data, x_max, y_max, red_robot_name=PLAYER_ROBOT_NAME, blue_robot_name=ENEMY_ROBOT_NAME, title="Current Game State", is_show=False)
            fig_placeholder.pyplot(fig, use_container_width=True)

    left_col, right_col = st.columns(2)

    # ------------------------------------------------------------------------
    # 左カラム ― コード編集 & 相手ロボ選択
    # ------------------------------------------------------------------------
    with left_col:
        st.subheader("Display Options")
        display_option = st.selectbox("Choose what to display:",
                                    ["Edit Code", "Highlighted Code"])

        if display_option == "Edit Code":
            code = st.text_area("Python Code",
                                st.session_state["robot_code"],
                                height=750)
            st.session_state["robot_code"] = code
        else:
            st.code(st.session_state["robot_code"], language="python")

        st.subheader("Select Opponent Robot")
        robots_dir   = os.path.join(os.path.dirname(__file__), "../robots")
        robot_files  = [f for f in os.listdir(robots_dir) if f.endswith(".py")]
        selected_robot = st.selectbox("Choose a robot:", robot_files)

        if selected_robot:
            with open(os.path.join(robots_dir, selected_robot), "r") as file:
                robot_code_text = file.read()
            st.subheader(f"Selected Robot: {selected_robot}")
            st.code(robot_code_text, language="python")
        else:
            robot_code_text = ""        # 空文字で安全にしておく

    # ------------------------------------------------------------------------
    # 右カラム ― ゲーム進行
    # ------------------------------------------------------------------------
    with right_col:

        # ----------------- ボタン群 -----------------
        cols_btn = st.columns(2)
        run_turn_clicked  = cols_btn[0].button("Run Turn")
        reset_clicked     = cols_btn[1].button("Reset Game")

        # ----------------- リセット -----------------
        if reset_clicked:
            controller.reset()
            st.session_state["show_initial_state"]     = True
            st.session_state["last_opponent_action"]   = None
            st.success("Game reset. Press Run Turn to begin.")
            st.stop()                              # 以降の描画を止めてページ再描画

        # ----------------- 初期状態表示 -----------------
        if st.session_state["show_initial_state"]:
            st.subheader("Initial Game State")
            st.write(controller.game_state[0])
            st.write(controller.game_state[-1])

        # ----------------- ゲーム終了判定 -----------------
        if player.hp <= 0 or enemy.hp <= 0:
            loser = "Player Robot" if player.hp <= 0 else "Opponent Robot"
            st.warning(f"Game Over! **{loser}** has 0 HP.")
            if run_turn_clicked:           # 終了後に Run Turn を押されたら無視
                st.info("Press **Reset Game** to start a new match.")
            # Run Turn 以降の処理を行わない
            run_turn_clicked = False

        # ----------------- Run Turn 本体 -----------------
        if run_turn_clicked:
            st.session_state["show_initial_state"] = False   # 初期表示を今後は出さない

            # 1) ユーザ側ロジックを exec
            try:
                exec_globals = {}
                exec(st.session_state["robot_code"], exec_globals)
                robot_logic_fn = exec_globals.get("robot_logic")
                if not robot_logic_fn:
                    st.error("Left pane code に robot_logic() が見つかりません。")
                    st.stop()
                player.robot_logic = robot_logic_fn
            except Exception:
                st.error(f"Error in player code:\n{traceback.format_exc()}")
                st.stop()

            # 2) 敵ロボロジックを exec
            try:
                opp_globals = {}
                exec(robot_code_text, opp_globals)
                opponent_logic_fn = opp_globals.get("robot_logic")
                if not opponent_logic_fn:
                    st.error("Opponent robot code に robot_logic() が見つかりません。")
                    st.stop()
                enemy.robot_logic = opponent_logic_fn
            except Exception:
                st.error(f"Error in opponent code:\n{traceback.format_exc()}")
                st.stop()

            # 3) プレイヤーターン
            game_info = controller.build_game_info(player)
            if game_info is not None:
                player_action, player_memo = controller.run_logic(player)
                controller.save_game_state(player.name, player_action)
                controller.turn += 1
                st.success("Player turn executed!")
                st.write("Player Action:", player_action)
                st.write("Player Memo:", player_memo)
                st.write("Game State after Player:", controller.game_state[-1])
            else:
                st.warning("No valid game_info for Player ‒ turn skipped.")

            # 4) 敵ターン
            game_info = controller.build_game_info(enemy)
            if game_info is not None:
                opponent_action, opponent_memo = controller.run_logic(enemy)
                controller.save_game_state(enemy.name, opponent_action)
                controller.turn += 1
                st.session_state["last_opponent_action"] = opponent_action
                st.write("Opponent Action:", opponent_action)
                st.write("Opponent Memo:", opponent_memo)
                st.write("Game State after Opponent:", controller.game_state[-1])
            else:
                st.warning("No valid game_info for Opponent ‒ turn skipped.")

            # 再描画処理
            if controller.game_state:
                current_turn_data = controller.game_state[-1]
                if "robots" in current_turn_data:
                    fig = draw_board(current_turn_data, x_max, y_max, red_robot_name=PLAYER_ROBOT_NAME, blue_robot_name=ENEMY_ROBOT_NAME, title="Current Game State", is_show=False)
                    fig_placeholder.pyplot(fig, use_container_width=True)  # 上部の画像を更新

        # ----------------- 直前の敵アクション -----------------
        if st.session_state["last_opponent_action"] is not None:
            st.subheader("Last Opponent Action")
            st.write(st.session_state["last_opponent_action"])


if __name__ == "__main__":
    main()