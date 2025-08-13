import sys
sys.path.append('./')

from pcrb.robot import Robot
from pcrb.controller import GameController
from pcrb.constants import PLAYER_ROBOT_NAME

def robot_logic_super_rest(robot, game_info, memos):
    # 1ターン目はsuper_rest、2ターン目は攻撃
    if not memos:
        return "super_rest"
    else:
        return "attack"

def robot_logic_attack(robot, game_info, memos):
    # 常に攻撃
    return "attack"

def test_super_rest():
    controller = GameController()
    robot1 = Robot(PLAYER_ROBOT_NAME, 1, 3, robot_logic_super_rest, controller)
    robot2 = Robot("Robot B", 2, 3, robot_logic_attack, controller)
    controller.set_robots(robot1, robot2)

    # 初期SP
    initial_sp = robot1.sp
    # 1ターン目: super_restでSP回復
    controller.run_logic(robot1)
    assert robot1.sp > initial_sp, "SP should increase after super_rest."
    # 1ターン目: robot2が攻撃
    controller.run_logic(robot2)
    # ダメージ1.5倍が適用されているか
    expected_damage = robot2.attack.power * 1.5
    actual_damage = initial_sp + 30 - robot1.sp  # SP回復後の攻撃で減った分
    assert abs(robot1.hp - (100 - expected_damage)) < 1e-3, "Damage should be 1.5x after super_rest."
    # 2ターン目: super_rest効果が解除されているか
    robot1_hp_before = robot1.hp
    controller.run_logic(robot1)  # 2ターン目は攻撃
    controller.run_logic(robot2)  # 2ターン目も攻撃
    # ダメージが通常通りか
    normal_damage = robot2.attack.power
    assert abs(robot1.hp - (robot1_hp_before - normal_damage)) < 1e-3, "Damage should be normal after super_rest reset."

if __name__ == "__main__":
    test_super_rest()
