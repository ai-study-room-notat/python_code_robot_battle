from .utils import is_valid_memo
from .robot import Robot
from .controller import GameController
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME


def robot_logic(robot, game_info, memos):
    # スタミナが少ない場合は休み、それ以外は敵に近づいて攻撃
    enemy_position = game_info['enemy_position']
    memo = {}
    if robot.sp < 20:
        return "rest", memo
    elif abs(robot.position[0] - enemy_position[0]) + abs(robot.position[1] - enemy_position[1]) == 1:
        return "attack", memo
    else:
        if robot.position[0] < enemy_position[0]:
            return "right", memo
        elif robot.position[0] > enemy_position[0]:
            return "left", memo
        elif robot.position[1] < enemy_position[1]:
            return "down", memo
        else:
            return "up", memo


def main():
    controller = GameController()

    _x = controller.robot1_initial_position['x']
    _y = controller.robot1_initial_position['y']
    robot1 = Robot(PLAYER_ROBOT_NAME, _x, _y, robot_logic, controller)

    _x = controller.robot2_initial_position['x']
    _y = controller.robot2_initial_position['y']
    robot2 = Robot(ENEMY_ROBOT_NAME, _x, _y, robot_logic, controller)

    controller.set_robots(robot1, robot2)
    controller.game_loop()


if __name__ == "__main__":
    main()
