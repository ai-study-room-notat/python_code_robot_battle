import sys

sys.path.append('./')

from pcrb.robot import Robot
from pcrb.controller import GameController
from pcrb.constants import PLAYER_ROBOT_NAME


def robot_logic(robot, game_info, memos):
    """テスト用ロジック: 罠を設置し、敵が罠にかかるように誘導"""
    enemy_position = game_info['enemy_position']
    robot_position = robot.position

    # スタミナが少ない場合は休む
    if robot.sp < 15:
        return "rest"

    # 罠を設置する
    if not memos:
        return "trap_right", {}  # 右方向に罠を設置

    # 敵が罠の位置にいない場合、罠の位置に誘導する
    trap_position = (robot_position[0] + 1, robot_position[1])  # 右隣の位置
    if enemy_position != trap_position:
        if enemy_position[0] < trap_position[0]:
            return "right"
        elif enemy_position[0] > trap_position[0]:
            return "left"
        elif enemy_position[1] < trap_position[1]:
            return "down"
        else:
            return "up"

    # 敵が罠の位置にいる場合、攻撃する
    return "attack"


def test_trap():
    controller = GameController()

    # ロボット1の初期位置
    robot1 = Robot(PLAYER_ROBOT_NAME, 1, 3, robot_logic, controller)

    # ロボット2の初期位置
    robot2 = Robot("Robot B", 3, 3, robot_logic, controller)

    controller.set_robots(robot1, robot2)

    initial_hp_robot1 = robot1.hp
    initial_hp_robot2 = robot2.hp

    trap_triggered = False  # 罠が発動したかどうかを追跡

    # ゲームループを1ターンずつ進めて罠の効果を確認
    for _ in range(10):  # 最大10ターン実行
        controller.run_logic(robot1)
        controller.run_logic(robot2)

        # ログを確認
        print(f"Turn {controller.turn}: {PLAYER_ROBOT_NAME} Position: {robot1.position}, Robot B Position: {robot2.position}")
        print(f"{PLAYER_ROBOT_NAME} Traps: {robot1.trap.traps}, Robot B Traps: {robot2.trap.traps}")

        # 敵が罠にかかった場合、HPの減少を確認
        if robot1.hp < initial_hp_robot1:
            print(f"{PLAYER_ROBOT_NAME} stepped on a trap! HP: {robot1.hp}")
            assert robot1.hp < initial_hp_robot1, f"{PLAYER_ROBOT_NAME}'s HP should decrease after stepping on a trap."
            assert (robot1.position not in robot2.trap.traps), "Trap should be removed after activation."
            trap_triggered = True
            break

        if robot2.hp < initial_hp_robot2:
            print(f"Robot B stepped on a trap! HP: {robot2.hp}")
            assert robot2.hp < initial_hp_robot2, "Robot B's HP should decrease after stepping on a trap."
            assert (robot2.position not in robot1.trap.traps), "Trap should be removed after activation."
            trap_triggered = True
            break

    # テスト終了時に罠が発動していなかった場合はエラーを発生
    assert trap_triggered, "No robot triggered a trap during the test!"


if __name__ == "__main__":
    test_trap()