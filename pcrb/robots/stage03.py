import random


def robot_logic(robot, game_info):
    # 往復と休憩をランダムに実施
    actions = ["left", "right", "rest"]
    return random.choice(actions)
