def robot_logic(robot, game_info, memos):
    """
    SuperRestと通常/遠距離攻撃を使い分けるロジック：
    - SPが30未満ならSuperRest
    - 敵が隣接していれば攻撃
    - 敵が2マス離れていれば遠距離攻撃
    - それ以外はRest
    """
    enemy_position = game_info['enemy_position']
    if enemy_position is None:
        return "rest"
    distance = abs(robot.position[0] - enemy_position[0]) + abs(robot.position[1] - enemy_position[1])
    if robot.sp < 30:
        return "super_rest"
    elif distance == 1 and robot.sp >= 10:
        return "attack"
    elif distance == 2 and robot.sp >= 15:
        return "ranged_attack"
    else:
        return "rest"
