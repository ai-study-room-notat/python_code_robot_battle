import json

from utils import is_valid_memo


class GameController:
    def __init__(
            self, max_turn=100, x_max=9, y_max=7, robot1_initial_position=None, robot2_initial_position=None):
        self.robot1 = None
        self.robot2 = None
        self.memos1 = []
        self.memos2 = []
        self.turn = 0
        self.max_turn = max_turn
        self.x_max = x_max
        self.y_max = y_max
        self.robot1_initial_position = {'x': 1, 'y': 3} if robot1_initial_position is None else robot1_initial_position
        self.robot2_initial_position = {'x': 7, 'y': 3} if robot2_initial_position is None else robot2_initial_position
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
        self.memos1 = []
        self.memos2 = []
        self.save_game_state(None, None)
        self.turn += 1

    def log_action(self, turn, message):
        print(message)
        self.log_file.write(f"Turn {turn}: {message}\n")

    def is_position_occupied(self, x, y):
        """指定された位置にロボットがいるかを確認"""
        return self.robot1.position == (x, y) or self.robot2.position == (x, y)
    
    def is_trap_at_position(self, x, y):
        """指定された位置にトラップがあるかを確認（自分または相手のトラップ）"""
        return (x, y) in self.robot1.trap.traps or (x, y) in self.robot2.trap.traps
    
    @staticmethod
    def adjust_action_for_robot1(action):
        return action

    @staticmethod
    def adjust_action_for_robot2(action):
        if action == "up":
            action = 'down'
        if action == "up":
            action = 'down'
        if action == "left":
            action = 'right'
        if action == "right":
            action = 'left'
        return action

    def run_logic(self, robot):
        enemy = self.robot1 if robot == self.robot2 else self.robot2
        memos = self.memos1 if robot == self.robot1 else self.memos2
        adjust_action = self.adjust_action_for_robot1 if robot == self.robot1 else self.adjust_action_for_robot2

        robot.trap.check_trap(enemy)  # 罠のチェック

        game_info = self.build_game_info(robot)

        response = robot.robot_logic(robot, game_info, memos)
        print(f"DEBUG: response from robot_logic: {response}, type: {type(response)}")

        if isinstance(response, str):
            action = response
            memo = {}
        elif isinstance(response, (list, tuple)) and len(response) == 2:
            action, memo = response
        else:
            assert False, f"Unexpected response format from robot_logic: {response} (type: {type(response)})"

        action = adjust_action(action)

        if robot == self.robot1:
            self.memos1.append(memo)
        else:
            self.memos2.append(memo)

        if robot.stun_counter > 0:
            print(f"DEBUG: Stunned. Returning ('stun')")

            return "stun", {}

        robot.start_turn()
        if action == "rest":
            robot.rest(self.turn)
        elif action == "super_rest":
            robot.super_rest(self.turn)
        elif action == "attack":
            robot.attack(enemy, self.turn)
        elif action == "defend":
            robot.defend(self.turn)
        elif action in ["up", "down", "left", "right"]:
            robot.move(action, self.turn)
        elif action == "ranged_attack":
            robot.ranged_attack(enemy, self.turn)
        elif action == "parry":
            robot.parry(self.turn)
        elif action in ["trap_up", "trap_down", "trap_left", "trap_right"]:
            robot.trap(action, self.turn)
        elif action == "steal":
            robot.steal(enemy, self.turn)
        elif action == "teleport":
            robot.teleport(self.turn)
        elif action == "camouflage":
            robot.camouflage(self.turn)
        elif action == "scan":
            robot.scan(self.turn)
        else:
            print(f"Invalid action: {action}")
            raise ValueError("Unexpected robot action detected!")

        print(f"DEBUG: Returning action: {action} (type: {type(action)})")
        return action, memo

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
                    "defense_mode": self.robot1.defend.is_active,
                },
                {
                    "name": self.robot2.name,
                    "position": self.robot2.position,
                    "hp": self.robot2.hp,
                    "sp": self.robot2.sp,
                    "defense_mode": self.robot2.defend.is_active,
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
            current_robot = self.robot1 if self.turn % 2 != 0 else self.robot2 # Robot1 (A) が先攻になるように変更
            self.log_action(self.turn, f"\n--- Turn {self.turn} : {current_robot.name} turn ---")
            action, _ = self.run_logic(current_robot)
            self.save_game_state(current_robot.name, action)  # 各ターンごとの状態を保存
            self.log_action(self.turn, f" - {self.robot1.name} : HP: {self.robot1.hp}, SP: {self.robot1.sp}")
            self.log_action(self.turn, f" - {self.robot2.name} : HP: {self.robot2.hp}, SP: {self.robot2.sp}")
            self.turn += 1

        winner = self.robot1 if self.robot1.hp > self.robot2.hp else self.robot2
        self.log_action(self.turn, f"\n{winner.name} wins!")
        self.log_file.close()

        json.dump(self.game_state, self.game_state_file, indent=4)
        self.game_state_file.close()
        return winner, self.game_state

    def build_game_info(self, robot):
        """
        指定した robot から見たゲーム状況を辞書で返す。
        ・スキャン中なら敵 SP や罠の座標も渡す
        ・敵がカモフラージュ中で、自分がスキャンしていない場合は
          敵の位置を None にして隠す
        """
        enemy = self.robot1 if robot is self.robot2 else self.robot2

        info = {
            "turn":            self.turn,
            "enemy_hp":        enemy.hp,
            "enemy_position":  enemy.position,   # 後で条件付きで None にする
            "max_turn":        self.max_turn,
            "board_size":      {"x_max": self.x_max, "y_max": self.y_max},
        }

        # カモフラージュによる位置隠蔽
        if not robot.scan.is_active and enemy.camouflage.is_active:
            info["enemy_position"] = enemy.camouflage.last_known_position  # 最後に知られている位置を使用

        # スキャンしていれば追加情報を開示
        if robot.scan.is_active:
            info["enemy_sp"]    = enemy.sp
            info["enemy_traps"] = enemy.trap.traps.copy()

        return info

    def reset(self):
        """試合を完全リセットして新しいゲームを開始できるようにする"""

        # 1) ターンとメモをクリア
        self.turn   = 0
        self.memos1 = []
        self.memos2 = []

        # 2) ロボットを初期位置・初期ステータスに戻す
        for robot, init_pos in (
            (self.robot1, self.robot1_initial_position),
            (self.robot2, self.robot2_initial_position),
        ):
            if robot is not None:
                # Robot クラス内の reset に委譲
                robot.reset(init_pos["x"], init_pos["y"])

        # 3) ゲームステートを初期化
        self.game_state = [{
            "settings": {
                "max_turn": self.max_turn,
                "x_max":    self.x_max,
                "y_max":    self.y_max,
            }
        }]

        # 4) ログファイル／ステートファイルをクリア（追記でなく新規）
        if not self.log_file.closed:
            self.log_file.close()
        self.log_file = open("game_log.txt", "w")

        if not self.game_state_file.closed:
            self.game_state_file.close()
        self.game_state_file = open("game_state.json", "w")

        # 5) 完了メッセージ（任意）
        print("[GameController] Reset complete. Ready for a new match.")