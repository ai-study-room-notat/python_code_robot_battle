import random


def robot_logic(robot, game_info, memos):
    # 往復と休憩をランダムに実施
    actions = ["left", "right", "rest"]
    action = random.choice(actions)
    return action
