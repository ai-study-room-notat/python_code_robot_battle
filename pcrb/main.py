import json


class Robot:
    def __init__(self, name, x, y, robot_logic_function, controller):
        self._name = name
        self._x = x
        self._y = y
        self._hp = 100
        self._sp = 50
        self._attack_power = 20
        self._attack_cost = 10
        self._move_cost = 5
        self._rest_recovery = 15
        self._defense_mode = False
        self._defense_reduction = 0.5  # 防御中のダメージ軽減率
        self._defense_cost = 10  # 防御のコスト
        self._ranged_attack_cost = 15  # 遠距離攻撃のコスト
        self._ranged_attack_power = 15  # 遠距離攻撃の威力
        self.robot_logic = robot_logic_function
        self.controller = controller

    @property
    def name(self):
        return self._name

    @property
    def hp(self):
        return self._hp

    @property
    def sp(self):
        return self._sp

    @property
    def position(self):
        return self._x, self._y

    def take_damage(self, damage):
        if self._defense_mode:
            damage *= self._defense_reduction
        self._hp -= max(damage, 0)
        if self._hp <= 0:
            print(f"{self._name} has been destroyed!")
        return damage

    def move(self, direction, turn):
        if self._sp < self._move_cost:
            self.controller.log_action(turn, f"{self._name} does not have enough SP to move!")
            return

        # 移動先の座標を計算
        if direction == "up":
            new_x, new_y = self._x, max(0, self._y - 1)
        elif direction == "down":
            new_x, new_y = self._x, min(self.controller.y_max - 1, self._y + 1)
        elif direction == "left":
            new_x, new_y = max(0, self._x - 1), self._y
        elif direction == "right":
            new_x, new_y = min(self.controller.x_max - 1, self._x + 1), self._y
        else:
            self.controller.log_action(turn, f"{self._name} tried to move in an invalid direction.")
            return

        # 移動先に他のロボットがいないかチェック
        if self.controller.is_position_occupied(new_x, new_y):
            self.controller.log_action(
                turn, f"{self._name} tried to move to ({new_x}, {new_y}), but the path is blocked.")
        else:
            self._x, self._y = new_x, new_y
            self._sp -= self._move_cost
            self.controller.log_action(
                turn, f"{self._name} moved {direction} to ({self._x}, {self._y}), HP: {self._hp}, SP: {self._sp}")

    def attack(self, other_robot, turn):
        if self._sp >= self._attack_cost:
            if abs(self._x - other_robot._x) + abs(self._y - other_robot._y) == 1:
                damage = other_robot.take_damage(self._attack_power)
                self._sp -= self._attack_cost
                self.controller.log_action(turn, f"{self._name} attacks {other_robot.name} at ({other_robot._x}, {other_robot._y}) for {damage} damage.")
            else:
                self.controller.log_action(turn, f"{self._name} tried to attack a non-adjacent location.")
        else:
            self.controller.log_action(turn, f"{self._name} does not have enough SP to attack!")

    def defend(self, turn):
        if self._sp >= self._defense_cost:
            self._sp -= self._defense_cost
            self._defense_mode = True
            self.controller.log_action(turn, f"{self._name} is now in defense mode, reducing incoming damage.")
        else:
            self.controller.log_action(turn, f"{self._name} does not have enough SP to defend!")

    def start_turn(self):
        # 防御モードはターン開始時にリセット
        if self._defense_mode:
            print(f"{self._name} ends defense mode.")
            self._defense_mode = False

    def ranged_attack(self, target, turn):
        distance = abs(self._x - target._x) + abs(self._y - target._y)
        if distance == 2:
            if self._sp >= self._ranged_attack_cost:
                self._sp -= self._ranged_attack_cost
                damage = target.take_damage(self._ranged_attack_power)
                self.controller.log_action(turn, f"{self._name} performs a ranged attack on {target.name} for {damage} damage!")
            else:
                self.controller.log_action(turn, f"{self._name} does not have enough SP to perform a ranged attack!")
        else:
            self.controller.log_action(turn, f"{self._name} cannot perform a ranged attack on {target.name} due to incorrect distance (distance: {distance}).")

    def rest(self, turn):
        self._sp += self._rest_recovery
        self.controller.log_action(turn, f"{self._name} rests and recovers {self._rest_recovery} SP. Total SP: {self._sp}")

    def is_alive(self):
        return self._hp > 0

    def status(self):
        print(f"{self._name}: HP={self._hp}, SP={self._sp}, Position=({self._x}, {self._y})")

class GameController:
    def __init__(self, max_turn=100, x_max=9, y_max=9):
        self.robot1 = None
        self.robot2 = None
        self.turn = 0
        self.max_turn = max_turn
        self.x_max = x_max
        self.y_max = y_max
        self.log_file = open("game_log.txt", "w")
        self.game_state_file = open("game_state.json", "w")

        self.game_state = [{
            'settings': {
                'max_turn': self.max_turn,
                'x_max': self.x_max,
                'y_max': self.y_max,
            }
        }]

    def set_robots(self, robot1, robot2):
        self.robot1 = robot1
        self.robot2 = robot2

    def log_action(self, turn, message):
        print(message)
        self.log_file.write(f"Turn {turn}: {message}\n")

    def is_position_occupied(self, x, y):
        return self.robot1.position == (x, y) or self.robot2.position == (x, y)

    def run_logic(self, robot):
        enemy = self.robot2 if robot == self.robot1 else self.robot1
        enemy_position = enemy.position

        game_info = {'enemy_position': enemy_position}
        action = robot.robot_logic(robot, game_info)

        robot.start_turn()
        if action == "rest":
            robot.rest(self.turn)
        elif action == "attack":
            robot.attack(enemy, self.turn)
        elif action == "defend":
            robot.defend(self.turn)
        elif action in ["up", "down", "left", "right"]:
            robot.move(action, self.turn)
        elif action == "ranged_attack":
            robot.ranged_attack(enemy, self.turn)
        else:
            raise ValueError("Unexpected robot action detected!")

        return action

    def save_game_state(self, robot_name, action):
        # 現在のターンのゲーム状態を辞書形式で記録
        state = {
            "turn": self.turn,
            "robots": [
                {
                    "name": self.robot1.name,
                    "position": self.robot1.position,
                    "hp": self.robot1.hp,
                    "sp": self.robot1.sp,
                    "defense_mode": self.robot1._defense_mode,
                },
                {
                    "name": self.robot2.name,
                    "position": self.robot2.position,
                    "hp": self.robot2.hp,
                    "sp": self.robot2.sp,
                    "defense_mode": self.robot2._defense_mode,
                }
            ],
            'action': {
                'robot_name': robot_name,
                'action': action
            }
        }
        self.game_state.append(state)

    def game_loop(self):
        while self.robot1.is_alive() and self.robot2.is_alive() and self.turn < self.max_turn:
            current_robot = self.robot1 if self.turn % 2 == 0 else self.robot2
            self.log_action(self.turn, f"\n--- Turn {self.turn} : {current_robot.name} turn ---")
            action = self.run_logic(current_robot)
            self.save_game_state(current_robot.name, action)  # 各ターンごとの状態を保存
            self.log_action(self.turn, f" - {self.robot1.name} : HP: {self.robot1._hp}, SP: {self.robot1._sp}")
            self.log_action(self.turn, f" - {self.robot2.name} : HP: {self.robot2._hp}, SP: {self.robot2._sp}")
            self.turn += 1

        winner = self.robot1 if self.robot1.hp > self.robot2.hp else self.robot2
        self.log_action(self.turn, f"\n{winner.name} wins!")
        self.log_file.close()

        json.dump(self.game_state, self.game_state_file, indent=4)
        self.game_state_file.close()
        return winner


def robot_logic(robot, game_info):
    # スタミナが少ない場合は休み、それ以外は敵に近づいて攻撃
    enemy_position = game_info['enemy_position']
    if robot.sp < 20:
        return "rest"
    elif abs(robot.position[0] - enemy_position[0]) + abs(robot.position[1] - enemy_position[1]) == 1:
        return "attack"
    else:
        if robot.position[0] < enemy_position[0]:
            return "right"
        elif robot.position[0] > enemy_position[0]:
            return "left"
        elif robot.position[1] < enemy_position[1]:
            return "down"
        else:
            return "up"


def main():
    controller = GameController(max_turn=100, x_max=9, y_max=7)
    robot1 = Robot("Robot A", 1, 3, robot_logic, controller)
    robot2 = Robot("Robot B", 7, 3, robot_logic, controller)
    controller.set_robots(robot1, robot2)
    controller.game_loop()


if __name__ == "__main__":
    main()
