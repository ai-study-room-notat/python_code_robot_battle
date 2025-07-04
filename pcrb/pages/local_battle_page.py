import streamlit as st
import importlib.util
import os
import traceback
import pandas as pd
import json
import base64
import io
import zipfile

import sys
sys.path.append('./pcrb')

from app import is_safe_code, load_player_module, play_game, game_state_download_button
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME

ROBOTS_DIR = "./pcrb/robots"

ROBOT1_NAME = "Robot 1"
ROBOT2_NAME = "Robot 2"

def upload_robot_logic(label: str):
    """
    指定されたラベルでファイルアップローダーを表示し、ロボットのPythonロジックファイルをアップロードさせます。
    アップロードされたファイルの内容を表示し、安全性をチェックします。
    安全であれば、モジュールとしてロードし、robot_logic関数を返します。
    エラーが発生した場合はNoneを返します。
    """
    uploaded_file = st.file_uploader(label, type=["py"], key=f"uploader_{label.replace(' ', '_')}")
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

def main():
    st.title("Local Battle Page")
    st.write("---")
    st.markdown(
        f"""
        このページでは、あなたが用意した2つのロボットのロジックファイルをアップロードし、
        指定した回数だけ対戦させることができます。

        **{ROBOT1_NAME}（先攻） vs {ROBOT2_NAME}（後攻）で対戦します。**
        """
    )
    st.write("---")

    # --- ロボットロジックのアップロード (2段組) ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"🤖 {ROBOT1_NAME} (先攻)")
        robot1_logic, robot1_code = upload_robot_logic(f"Upload {ROBOT1_NAME} Logic (.py)")

    with col2:
        st.subheader(f"🤖 {ROBOT2_NAME} (後攻)")
        robot2_logic, robot2_code = upload_robot_logic(f"Upload {ROBOT2_NAME} Logic (.py)")

    st.write("---")

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

            # Initialize progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i in range(battle_rounds):
                status_text.text(f"Running Round {i+1}/{battle_rounds}...")
                winner, game_state = play_game(robot1_logic, robot2_logic, ROBOT1_NAME, ROBOT2_NAME)

                if winner.name == ROBOT1_NAME:
                    st.session_state.robot1_wins += 1
                    round_winner_for_df = ROBOT1_NAME
                elif winner.name == ROBOT2_NAME:
                    st.session_state.robot2_wins += 1
                    round_winner_for_df = ROBOT2_NAME
                else:
                    st.session_state.draws += 1
                    round_winner_for_df = "Draw"

                st.session_state.local_battle_results.append({
                    "Round": i + 1,
                    "Winner": round_winner_for_df,
                    # "Result": result_str,  # ← 不要なので削除
                    "game_state": game_state
                })
                progress_bar.progress((i + 1) / battle_rounds)

            status_text.text("All rounds complete!")
            st.write("--- Battle Summary ---")
            st.markdown(f"**{ROBOT1_NAME} Wins:** {st.session_state.robot1_wins}")
            st.markdown(f"**{ROBOT2_NAME} Wins:** {st.session_state.robot2_wins}")
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
            download_link = f'<a href="data:application/json;base64,{b64}" download="{log_filename}">Download Log</a>'

            display_data.append({
                "Round": res["Round"],
                "Winner": res["Winner"],
                # "Result": res["Result"],  # ← 不要なので削除
                "Log": download_link
            })

        results_df = pd.DataFrame(display_data)
        st.markdown(results_df[["Round", "Winner", "Log"]].to_html(escape=False, index=False), unsafe_allow_html=True)

        st.write("---")

        # --- 全ログ一括ダウンロードボタン ---
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for res in st.session_state.local_battle_results:
                log_filename = f"local_battle_round_{res['Round']}_log.json"
                game_state_json_str = json.dumps(res["game_state"], ensure_ascii=False, indent=4)
                zip_file.writestr(log_filename, game_state_json_str)

        zip_buffer.seek(0)
        st.download_button(
            label="Download All Logs (ZIP)",
            data=zip_buffer,
            file_name="local_battle_all_logs.zip",
            mime="application/zip",
            key="download_all_logs_zip"
        )

if __name__ == "__main__":
    main()
