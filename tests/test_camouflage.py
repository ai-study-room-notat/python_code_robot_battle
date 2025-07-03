import sys

sys.path.append('./pcrb')

from robot import Robot
from controller import GameController
from pcrb.constants import PLAYER_ROBOT_NAME


def robot_logic(robot, game_info, memos):
    """テスト用ロジック: 最初のターンでカモフラージュを使用し、次のターンで右に移動"""
    print("game_info['turn'] :", game_info['turn'])
    if game_info['turn'] == 1 and robot.sp >= 20 and not robot.camouflage.is_active:
        return "camouflage"
    elif game_info['turn'] == 2:
        return "right"
    return "rest"


def test_camouflage():
    controller = GameController()

    # ロボット1の初期位置
    robot1 = Robot(PLAYER_ROBOT_NAME, 1, 3, robot_logic, controller)

    # ロボット2の初期位置
    robot2 = Robot("Robot B", 7, 3, robot_logic, controller)

    controller.set_robots(robot1, robot2)

    # 初期状態の確認
    assert not robot1.camouflage.is_active, f"{PLAYER_ROBOT_NAME} should not be camouflaged initially."
    assert not robot2.camouflage.is_active, "Robot B should not be camouflaged initially."

    # ターン0: カモフラージュを使用
    controller.run_logic(robot1)
    controller.turn += 1
    assert robot1.camouflage.is_active, f"{PLAYER_ROBOT_NAME} should be camouflaged after using camouflage."
    assert robot1.camouflage.remaining_turns == 3, "Camouflage duration should be 3 turns."
    game_info = controller.build_game_info(robot2)
    assert game_info["enemy_position"] == (1, 3), "Enemy position should be the last known position when camouflaged."

    # ターン1: 右に移動
    controller.run_logic(robot1)
    controller.turn += 1
    game_info = controller.build_game_info(robot2)
    assert robot1.camouflage.is_active, "Camouflage should remain active during its duration."
    assert game_info["enemy_position"] == (1, 3), "Enemy position should remain the last known position during camouflage."

    # カモフラージュの持続ターンをシミュレート
    for _ in range(1):  # 残りの持続ターンを進める
        controller.run_logic(robot1)
        controller.turn += 1
        game_info = controller.build_game_info(robot2)
        assert robot1.camouflage.is_active, "Camouflage should remain active during its duration."
        assert game_info["enemy_position"] == (1, 3), "Enemy position should remain the last known position during camouflage."

    # カモフラージュが終了したことを確認
    controller.run_logic(robot1)
    controller.turn += 1
    assert not robot1.camouflage.is_active, "Camouflage should no longer be active after its duration ends."
    game_info = controller.build_game_info(robot2)
    assert game_info["enemy_position"] == (2, 3), "Enemy position should update to the current position after camouflage ends."


if __name__ == "__main__":
    test_camouflage()