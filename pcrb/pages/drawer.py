import json
import streamlit as st

import sys
sys.path.append('./pcrb')

from draw import draw_board_v2 as draw_board
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME

def st_draw_board(data):
    title_holder = st.empty()
    turn_slider_holder = st.empty()
    turn_button_holder = st.empty()
    board_holder = st.empty()
    robots_holder = st.empty()
    # memo_holder = st.empty()

    settings = data[0]['settings']
    # max_turn = settings['max_turn']
    x_max = settings['x_max']
    y_max = settings['y_max']

    # memo_holder.write(max_turn)
    # st.sidebar.write("Debug info:", data)
    all_turn_data = data[1:]

    # Initialize session state for the current turn
    if 'current_turn' not in st.session_state:
        st.session_state.current_turn = 0

    # Slider for selecting turn
    max_turn = all_turn_data[-1]['turn']

    # Next and Back buttons
    col1, col2, _ = turn_button_holder.columns([1, 1, 2])
    with col1:
        back_clicked = st.button("Back", key="btn_back", use_container_width=True)
    with col2:
        next_clicked = st.button("Next", key="btn_next", use_container_width=True)

    if back_clicked:
        st.session_state.current_turn = max(
            0, st.session_state.current_turn - 1
        )
    if next_clicked:
        st.session_state.current_turn = min(
            max_turn, st.session_state.current_turn + 1
        )

    # ---------- スライダー ----------
    turn_slider_holder.slider(
        "TURN",
        0,
        max_turn,
        key="current_turn"
    )

    # Sync slider with button actions
    turn_id = st.session_state.current_turn
    turn_data = all_turn_data[turn_id]

    _action = turn_data['action']
    _robots = turn_data['robots']

    robots_holder.write(_robots)

    title = f"Turn {turn_data['turn']} - Action: {_action['robot_name']} -> {_action['action']}"
    title_holder.header(title)

    # 先攻・後攻ロボット名をログから取得
    if len(all_turn_data) > 0 and 'robots' in all_turn_data[0]:
        red_robot_name = all_turn_data[0]['robots'][0]['name']
        blue_robot_name = all_turn_data[0]['robots'][1]['name']
    else:
        red_robot_name = PLAYER_ROBOT_NAME
        blue_robot_name = ENEMY_ROBOT_NAME

    fig = draw_board(turn_data, x_max, y_max, red_robot_name=red_robot_name, blue_robot_name=blue_robot_name, title='', is_show=False)
    board_holder.pyplot(fig)


def main():
    st.title("Drawer Page") 
    st.caption("対戦ログをアップロードして、ボードを描画します。")
    uploaded_file = st.file_uploader("Upload game_state.json", type="json")

    if uploaded_file is not None:
        data = json.load(uploaded_file)
        st_draw_board(data)


if __name__ == '__main__':
    main()