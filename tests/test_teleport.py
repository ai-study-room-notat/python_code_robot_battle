import sys
import random

sys.path.append('./')

from pcrb.robot import Robot
from pcrb.controller import GameController
from pcrb.constants import PLAYER_ROBOT_NAME


def robot_logic(robot, game_info, memos):
    """テスト用ロジック: テレポートを実行"""
    if robot.sp >= 20:
        return "teleport"
    return "rest"


def test_teleport():
    controller = GameController()

    # ロボットの初期位置
    robot_a = Robot(PLAYER_ROBOT_NAME, 1, 1, robot_logic, controller)
    robot_b = Robot("Robot B", 1, 2, robot_logic, controller)

    controller.set_robots(robot_a, robot_b)

    initial_sp = robot_a.sp
    initial_position = robot_a.position

    # テレポートを実行
    random.seed(42)  # テストの再現性を確保するために乱数シードを設定
    controller.run_logic(robot_a)

    # テレポート後の位置とスタミナを確認
    assert robot_a.sp == initial_sp - 20, "Robot A should have consumed 20 SP for teleport."
    assert robot_a.position != initial_position, "Robot A should have teleported to a new position."
    assert 0 <= robot_a.x < controller.x_max and 0 <= robot_a.y < controller.y_max, "Robot A should teleport within the field boundaries."

    print(f"Robot A teleported to {robot_a.position} with SP: {robot_a.sp}")


if __name__ == "__main__":
    test_teleport()