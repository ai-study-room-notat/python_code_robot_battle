import sys

sys.path.append('./pcrb')

import os
import pytest
import matplotlib.pyplot as plt
from pcrb.draw import draw_board_v2
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME

@pytest.fixture
def mock_turn_data():
    """モックのターンデータを生成"""
    def generate_turn_data(action):
        return {
            "action": {
                "robot_name": PLAYER_ROBOT_NAME,
                "action": action,
            },
            "robots": [
                {"name": PLAYER_ROBOT_NAME, "position": [4, 4]},
                {"name": "Robot B", "position": [6, 6]},
            ],
        }
    return generate_turn_data

@pytest.mark.parametrize("action", [
    "attack", "rest", "super_rest", "up", "down", "left", "right", "defend", "parry", 
    "ranged_attack", "trap_right", "steal", 
    "teleport", "camouflage", "scan"
])
def test_draw_board_v2(mock_turn_data, action):
    """draw_board_v2 の描画をテスト"""
    x_max, y_max = 9, 9
    turn_data = mock_turn_data(action)
    fig = draw_board_v2(turn_data, x_max, y_max, red_robot_name=PLAYER_ROBOT_NAME, blue_robot_name=ENEMY_ROBOT_NAME, title=f"Test Board - {action}", is_show=False)

    # 描画が成功しているか確認
    assert fig is not None, f"Figure should not be None for action: {action}"

    # 描画結果を保存して確認（デバッグ用）
    output_file = f"test_draw_board_v2_{action}.png"
    fig.savefig(output_file)
    assert os.path.exists(output_file), f"Output image should be saved for action: {action}"

    # 後片付け
    os.remove(output_file)