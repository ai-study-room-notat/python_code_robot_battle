import sys

sys.path.append('./')

from pcrb.robot import Robot
from pcrb.controller import GameController
from pcrb.constants import PLAYER_ROBOT_NAME


def robot_logic(robot, game_info, memos):
    """テスト用ロジック: スキャンを使用"""
    if game_info['turn'] == 2:
        assert 'enemy_sp' in game_info
        assert 'enemy_traps' in game_info

    if robot.sp >= 10 and not robot.scan.is_active:
        return "scan"
    return "rest"


def test_scan_with_logic():
    controller = GameController()

    # ロボット1の初期位置
    robot1 = Robot(PLAYER_ROBOT_NAME, 1, 3, robot_logic, controller)

    # ロボット2の初期位置
    robot2 = Robot("Robot B", 7, 3, robot_logic, controller)

    controller.set_robots(robot1, robot2)

    # 初期状態の確認
    assert not robot1.scan.is_active, f"{PLAYER_ROBOT_NAME} should not be scanning initially."
    assert not robot2.scan.is_active, "Robot B should not be scanning initially."

    # スキャンを使用
    controller.run_logic(robot1)

    # スキャンが有効になったことを確認
    assert robot1.scan.is_active, f"{PLAYER_ROBOT_NAME} should be scanning after using scan."
    assert robot1.scan.remaining_turns == 1, "Scan duration should be 1 turn."

    # スキャンの持続ターンをシミュレート
    robot1.start_turn()
    assert not robot1.scan.is_active, "Scan should no longer be active after its duration ends."

    # スキャンを使用
    controller.run_logic(robot1)


if __name__ == "__main__":
    test_scan_with_logic()