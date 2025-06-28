import random

# Ultimate Robot – invictus finalizer
# - Fix decisive‑push misfire: only step into distance‑1 when enough SP remains for
#   *either* immediate attack next turn (≥10 after move) or parry (≥parry_cost).
# - Re‑enable parry at distance‑1 when attack不可 but parry可 & enemy likely to attack.
# - Keep tempo‑sync rule.


def robot_logic(robot, game_info, memos):
    board = game_info.get("board_size", {})
    if isinstance(board, dict):
        x_max, y_max = board.get("x_max", 9), board.get("y_max", 7)
    else:
        x_max, y_max = 9, 7

    atk_cost   = getattr(robot.attack, "cost", 10)
    mov_cost   = getattr(robot.move,   "cost", 5)
    rng_cost   = getattr(getattr(robot, "ranged_attack", None), "cost", 999)
    parry_cost = getattr(getattr(robot, "parry", None), "cost", 999)
    scan_cost  = getattr(getattr(robot, "scan", None), "cost", 999)

    enemy_pos = game_info.get("enemy_position")
    enemy_hp  = game_info.get("enemy_hp")
    enemy_sp  = game_info.get("enemy_sp")
    traps     = set(tuple(t) for t in game_info.get("enemy_traps", []))

    my_x, my_y = robot.position
    can   = lambda c: robot.sp >= c
    in_bd = lambda x, y: 0 <= x < x_max and 0 <= y < y_max

    # -------- 探索 -------------------------------------------------
    if enemy_pos is None:
        if hasattr(robot, "scan") and can(scan_cost):
            return "scan"
        if not can(mov_cost):
            return "rest"
        for act,dx,dy in random.sample([("up",0,-1),("down",0,1),("left",-1,0),("right",1,0)],4):
            nx,ny = my_x+dx, my_y+dy
            if in_bd(nx,ny) and (nx,ny) not in traps:
                return act
        return "rest"

    ene_x, ene_y = enemy_pos
    dist = abs(my_x-ene_x) + abs(my_y-ene_y)

    # -------- 距離1 ------------------------------------------------
    if dist == 1:
        if can(atk_cost):
            return "attack"
        # 攻撃不可だがパリィ可能 & 敵が攻撃SP持ちならパリィ
        if can(parry_cost) and enemy_sp is not None and enemy_sp >= atk_cost \
           and getattr(robot.parry, "cooldown_counter", 0) == 0:
            return "parry"
        return "rest"

    # -------- 距離2 ------------------------------------------------
    if dist == 2:
        # Tempo‑sync: our SP10 vs enemy25 -> skip turn to align
        if robot.sp == 10 and enemy_sp == 25:
            return "rest"

        # 決定打: 敵HP<=40 で勝負を決めに行く
        if enemy_hp is not None and enemy_hp <= 40 and can(mov_cost):
            sp_after_move = robot.sp - mov_cost
            if sp_after_move >= atk_cost or (sp_after_move >= parry_cost and parry_cost < atk_cost):
                # choose safe axis first
                if my_x < ene_x and in_bd(my_x+1, my_y):
                    return "right"
                if my_x > ene_x and in_bd(my_x-1, my_y):
                    return "left"
                if my_y < ene_y and in_bd(my_x, my_y+1):
                    return "down"
                if my_y > ene_y and in_bd(my_x, my_y-1):
                    return "up"
        # 通常遠距離射撃
        if can(rng_cost):
            return "ranged_attack"
        return "rest"

    # -------- 距離>2 ----------------------------------------------
    if not can(mov_cost):
        return "rest"
    moves = []
    if my_x < ene_x: moves.append(("right", 1, 0))
    elif my_x > ene_x: moves.append(("left", -1, 0))
    if my_y < ene_y: moves.append(("down", 0, 1))
    elif my_y > ene_y: moves.append(("up", 0, -1))
    for act, dx, dy in moves:
        nx, ny = my_x + dx, my_y + dy
        if in_bd(nx, ny) and (nx, ny) not in traps:
            return act
    return "rest"
