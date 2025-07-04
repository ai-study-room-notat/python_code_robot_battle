import streamlit as st
import importlib.util
import os
import traceback
import pandas as pd
import json
import base64
import io # For BytesIO
import zipfile # For ZipFile

import sys
sys.path.append('./pcrb') # Execute from the root directory.

from app import is_safe_code, load_player_module, play_game, game_state_download_button

ROBOTS_DIR = "./pcrb/robots"

def upload_robot_logic(label: str):
    """
    指定されたラベルでファイルアップローダーを表示し、ロボットのPythonロジックファイルをアップロードさせます。
    アップロードされたファイルの内容を表示し、安全性をチェックします。
    安全であれば、モジュールとしてロードし、robot_logic関数を返します。
    エラーが発生した場合はNoneを返します。
    """
    uploaded_file = st.file_uploader(label, type=["py"], key=f"uploader_{label.replace(' ', '_')}") # Add unique key
    if uploaded_file:
        file_content = uploaded_file.read().decode("utf-8")
        with st.expander(f"View Uploaded Code for {label}", expanded=False):
            st.code(file_content, language="python")

        is_safe, message = is_safe_code(file_content)
        if not is_safe:
            st.error(f"Unsafe code detected in {label}: {message}")
            return None, None

        try:
            robot_logic = load_player_module(file_content)
            if robot_logic is None:
                st.error(f"`robot_logic` function not found in {label}. Please check the file.")
                return None, None
            return robot_logic, file_content
        except Exception as e:
            st.error(f"Error loading module from {label}: {e}")
            return None, None
    return None, None

def determine_battle_result(winner_name: str, robot1_name: str, robot2_name: str) -> tuple[str, str]:
    """
    対戦の勝者名とロボット1、ロボット2の名前を受け取り、
    結果文字列 (例: "勝利 🏆") と表示用の色 (例: "green") を返します。
    """
    if winner_name == robot1_name:
        return "勝利 🏆", "green"
    elif winner_name == robot2_name:
        return "敗北 ❌", "red"
    else: # play_gameが常にどちらかのロボット名を返すため、現状この分岐には到達しにくい
        return "引き分け ⚖️", "gray"

def main():
    st.title("Local Battle Page")
    st.write("---")
    st.markdown(
        """
        このページでは、あなたが用意した2つのロボットのロジックファイルをアップロードし、
        指定した回数だけ対戦させることができます。

        **Robot 1 (Player 1) が先攻、Robot 2 (Player 2) が後攻となります。**
        """
    )
    st.write("---")

    # --- ロボットロジックのアップロード (2段組) ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🤖 Robot 1 (Player 1)")
        robot1_logic, robot1_code = upload_robot_logic("Upload Robot 1 Logic (.py)")

    with col2:
        st.subheader("🤖 Robot 2 (Player 2)")
        robot2_logic, robot2_code = upload_robot_logic("Upload Robot 2 Logic (.py)")

    st.write("---") # Add a separator

    # --- 対戦回数の入力 ---
    st.subheader("⚔️ Battle Rounds")
    battle_rounds = st.number_input("Enter number of battle rounds (1-5):", min_value=1, max_value=5, value=1, step=1)

    # --- 対戦開始ボタン ---
    if st.button("Start Local Battle", disabled=(not robot1_logic or not robot2_logic)):
        if robot1_logic and robot2_logic:
            st.session_state.local_battle_results = []
            st.session_state.robot1_wins = 0
            st.session_state.robot2_wins = 0
            st.session_state.draws = 0

            robot1_name = "Robot Alpha"
            robot2_name = "Robot Beta"

            # Initialize progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i in range(battle_rounds):
                status_text.text(f"Running Round {i+1}/{battle_rounds}...")
                # play_gameのRobot Aがrobot1_logic、Robot Bがrobot2_logicに対応
                winner, game_state = play_game(robot1_logic, robot2_logic)

                round_winner_for_df = "" # For DataFrame ("Robot1" or "Robot2")

                if winner.name == "Robot A": # play_game内部のRobot Aは、このページではrobot1_logic (Robot Alpha) に対応
                    round_winner_for_df = "Robot1"
                    st.session_state.robot1_wins += 1
                elif winner.name == "Robot B": # play_game内部のRobot Bは、このページではrobot2_logic (Robot Beta) に対応
                    round_winner_for_df = "Robot2"
                    st.session_state.robot2_wins += 1
                else:
                    # 現状のplay_gameの実装では、必ずRobot AかRobot Bのインスタンスがwinnerとして返されるため、
                    # このelseブロックには到達しない想定。
                    round_winner_for_df = "Draw"
                    st.session_state.draws += 1

                # NOTE: Individual round winner text and download button are removed as per user request.
                # result_str, color = determine_battle_result(round_winner_display_name, robot1_name, robot2_name)
                # st.markdown(f"Round {i+1} Winner: <span style='color:{color}; font-weight:bold;'>{round_winner_display_name} ({result_str})</span>", unsafe_allow_html=True)
                # json_bytes = json.dumps(game_state, ensure_ascii=False, indent=4).encode("utf-8")
                # st.download_button(...)

                st.session_state.local_battle_results.append({
                    "Round": i + 1,
                    "Winner": round_winner_for_df,
                    "game_state": game_state # Store game_state for later download
                })
                progress_bar.progress((i + 1) / battle_rounds)

            status_text.text("All rounds complete!")
            st.write("--- Battle Summary ---")
            st.markdown(f"**{robot1_name} Wins:** {st.session_state.robot1_wins}")
            st.markdown(f"**{robot2_name} Wins:** {st.session_state.robot2_wins}")
            if st.session_state.draws > 0:
                st.markdown(f"**Draws:** {st.session_state.draws}")

    # --- 対戦結果の詳細表示 ---
    if 'local_battle_results' in st.session_state and st.session_state.local_battle_results:
        st.subheader("📊 Detailed Battle Results")

        # Prepare data for DataFrame, including download links
        display_data = []
        for res in st.session_state.local_battle_results:
            game_state_json = json.dumps(res["game_state"], ensure_ascii=False, indent=4)
            b64 = base64.b64encode(game_state_json.encode()).decode()
            log_filename = f"local_battle_round_{res['Round']}_log.json"
            # Use st.markdown for HTML link as st.download_button is tricky in a loop for DataFrame
            download_link = f'<a href="data:application/json;base64,{b64}" download="{log_filename}">Download Log</a>'

            display_data.append({
                "Round": res["Round"],
                "Winner": res["Winner"],
                "Log": download_link
            })

        results_df = pd.DataFrame(display_data)
        # Use st.markdown to render DataFrame with HTML links
        st.markdown(results_df[["Round", "Winner", "Log"]].to_html(escape=False, index=False), unsafe_allow_html=True)

        st.write("---") # Separator

        # --- 全ログ一括ダウンロードボタン ---
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for res in st.session_state.local_battle_results:
                log_filename = f"local_battle_round_{res['Round']}_log.json"
                # Add file to zip, data is game_state as json string
                game_state_json_str = json.dumps(res["game_state"], ensure_ascii=False, indent=4)
                zip_file.writestr(log_filename, game_state_json_str)

        zip_buffer.seek(0) # Reset buffer position to the beginning
        st.download_button(
            label="Download All Logs (ZIP)",
            data=zip_buffer,
            file_name="local_battle_all_logs.zip",
            mime="application/zip",
            key="download_all_logs_zip"
        )


if __name__ == "__main__":
    main()
