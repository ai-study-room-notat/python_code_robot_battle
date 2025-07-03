import streamlit as st

import sys
sys.path.append('./pcrb')

from app import is_safe_code
from app import load_player_module
from app import play_game
from app import game_state_download_button
from pages.drawer import st_draw_board
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME

# ----------------------------- メイン UI -----------------------------

def main() -> None:
    from robots.robot_03_random_walker import robot_logic as enemy_robot_logic

    st.set_page_config(page_title="PCRB", page_icon="🤖", layout="centered")

    # --- ヘッダー ---
    st.title("🤖 PCRB - PythonCodeRobotBattle")
    st.image("./pcrb/asset/title.png", use_container_width=True)
    st.caption("Python スクリプトでロボットを動かして対戦しよう！")
    st.write("---")

    # --- 概要セクション ---
    st.markdown(
        """
        **PCRB** へようこそ！  
        あなたが作成した Python スクリプトでロボットを操作し、対戦相手を倒すゲームです。  
        まずはサンプルスクリプトをダウンロードして、自分好みに改造してみましょう。  
        詳しい遊び方は左側サイドバーの **Manual** ページを参照してください。
        """
    )

    st.write("---")

    # --- 2 カラムレイアウト: ダウンロード & アップロード ---
    col_dl, col_ul = st.columns(2)

    # サンプルダウンロード
    with col_dl:
        st.subheader("サンプルスクリプト")
        sample_file_path = "samples/sample_robot_logic_file.py"
        with open(sample_file_path, "r", encoding="utf-8") as file:
            st.download_button(
                label="サンプルをダウンロード",
                data=file.read(),
                file_name="sample_robot_logic_file.py",
                mime="text/plain",
            )

    # スクリプトアップロード
    with col_ul:
        st.subheader("スクリプトをアップロード")
        uploaded_file = st.file_uploader(
            "robot_logic を含む Python ファイル (.py) を選択", type=["py"]
        )

    # --- アップロード後の処理 ---
    if uploaded_file:
        file_content = uploaded_file.read().decode("utf-8")

        with st.expander("アップロードされたコードを表示", expanded=False):
            st.code(file_content, language="python")

        # コード安全性チェック
        is_safe, message = is_safe_code(file_content)

        if not is_safe:
            st.error(f"⚠️ アップロードされたコードに問題があります: {message}")
            return

        # robot_logic をロード
        try:
            player_robot_logic = load_player_module(file_content)
            if player_robot_logic is None:
                st.error("`robot_logic` 関数が見つかりませんでした。ファイルを確認してください。")
                return
        except Exception as e:
            st.error(f"モジュールロード中にエラーが発生しました: {e}")
            return

        # --- ゲーム開始 ---
        if 'winner' not in st.session_state:
            st.success("✅ コードの読み込みに成功しました！ 対戦を開始します。")
            st.session_state.winner, st.session_state.game_state = play_game(player_robot_logic, enemy_robot_logic, PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME)

        if st.session_state.winner.name == PLAYER_ROBOT_NAME:
            if 'balloons_shown' not in st.session_state or not st.session_state.balloons_shown:
                st.balloons()
                st.session_state.balloons_shown = True
            st.header("🎉 勝利おめでとうございます！")
        else:
            st.header("🤖 残念！ 次の挑戦をお待ちしています。")

        # ゲーム結果ダウンロード
        st.subheader("ログとゲーム状態のダウンロード")
        st.write(f"ログ内では'{PLAYER_ROBOT_NAME}'があなたがアップロードしたロボットです。")
        game_state_download_button(st.session_state.game_state)

        # 盤面描画
        st_draw_board(st.session_state.game_state)


