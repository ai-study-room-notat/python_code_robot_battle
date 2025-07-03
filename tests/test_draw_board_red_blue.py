import os
import matplotlib.pyplot as plt
from pcrb.draw import draw_board
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME

def test_draw_board_red_blue_names():
    """red_robot_name, blue_robot_name の引数で描画が正しく行われるかテスト"""
    x_max, y_max = 9, 9
    turn_data = {
        "action": {"robot_name": PLAYER_ROBOT_NAME, "action": "attack"},
        "robots": [
            {"name": PLAYER_ROBOT_NAME, "position": [2, 2]},
            {"name": ENEMY_ROBOT_NAME, "position": [6, 6]},
        ],
    }
    fig = draw_board(turn_data, x_max, y_max, red_robot_name=PLAYER_ROBOT_NAME, blue_robot_name=ENEMY_ROBOT_NAME, title="Red/Blue Name Test", is_show=False)
    assert fig is not None, "Figure should not be None for red/blue robot name test"
    output_file = "test_draw_board_red_blue.png"
    fig.savefig(output_file)
    assert os.path.exists(output_file), "Output image should be saved for red/blue robot name test"
    os.remove(output_file)
