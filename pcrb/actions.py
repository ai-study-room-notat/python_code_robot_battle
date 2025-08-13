from abc import ABC
from abc import abstractmethod

from utils import is_adjacent


class Action(ABC):
    def __init__(self, actor, controller, **kwargs):
        super().__init__()
        self.actor = actor
        self.controller = controller

    @abstractmethod
    def __call__(self, **kwargs):
        """行動を実行するメソッド（子クラスで実装が必要）"""
        pass


class Attack(Action):
    power = 20
    cost = 10

    def __init__(self, actor, controller):
        super().__init__(actor, controller)

    def __call__(self, target, turn):
        if self.actor.sp >= self.cost:
            if is_adjacent(self.actor, target):
                if target.is_parrying():
                    self.actor.stun(1)
                else:
                    damage = target.receive_attack(self.power)
                    self.actor.use_sp(self.cost)
                    self.controller.log_action(turn, f"{self.actor.name} attacks {target.name} at ({target.x}, {target.y}) for {damage} damage.")
            else:
                self.controller.log_action(turn, f"{self.actor.name} tried to attack a non-adjacent location.")
        else:
            self.controller.log_action(turn, f"{self.actor.name} does not have enough SP to attack!")


class Move(Action):
    cost = 5

    def __init__(self, actor, controller):
        super().__init__(actor, controller)

    def __call__(self, direction, turn):
        if self.actor.sp < self.cost:
            self.controller.log_action(turn, f"{self.actor.name} does not have enough SP to move!")
            return

        # 移動先の座標を計算
        if direction == "up":
            new_x, new_y = self.actor.x, max(0, self.actor.y - 1)
        elif direction == "down":
            new_x, new_y = self.actor.x, min(self.controller.y_max - 1, self.actor.y + 1)
        elif direction == "left":
            new_x, new_y = max(0, self.actor.x - 1), self.actor.y
        elif direction == "right":
            new_x, new_y = min(self.controller.x_max - 1, self.actor.x + 1), self.actor.y
        else:
            self.controller.log_action(turn, f"{self.actor.name} tried to move in an invalid direction.")
            return

        # 移動先に他のロボットがいないかチェック
        if self.controller.is_position_occupied(new_x, new_y):
            self.controller.log_action(
                turn, f"{self.actor.name} tried to move to ({new_x}, {new_y}), but the path is blocked.")
        else:
            self.actor.set_position(new_x, new_y)
            self.actor.use_sp(self.cost)
            self.controller.log_action(
                turn, f"{self.actor.name} moved {direction} to ({self.actor.x}, {self.actor.y}), HP: {self.actor.hp}, SP: {self.actor.sp}")


class Defend(Action):
    reduction = 0.5  # 防御中のダメージ軽減率
    cost = 10  # 防御のコスト

    def __init__(self, actor, controller):
        super().__init__(actor, controller)
        self.is_active = False

    def __call__(self, turn):
        if self.actor.sp >= self.cost:
            self.actor.use_sp(self.cost)
            self.is_active = True
            self.controller.log_action(turn, f"{self.actor.name} is now in defense mode, reducing incoming damage.")
        else:
            self.controller.log_action(turn, f"{self.actor.name} does not have enough SP to defend!")

    def update(self):
        self.is_active = False


class RangedAttack(Action):
    cost = 15  # 遠距離攻撃のコスト
    power = 15  # 遠距離攻撃の威力

    def __init__(self, actor, controller):
        super().__init__(actor, controller)

    def __call__(self, target, turn):
        distance = abs(self.actor.x - target.x) + abs(self.actor.y - target.y)
        if distance == 2:
            if self.actor.sp >= self.cost:
                self.actor.use_sp(self.cost)
                damage = target.receive_attack(self.power)
                self.controller.log_action(
                    turn, f"{self.actor.name} performs a ranged attack on {target.name} for {damage} damage!")
            else:
                self.controller.log_action(
                    turn, f"{self.actor.name} does not have enough SP to perform a ranged attack!")
        else:
            self.controller.log_action(
                turn, f"{self.actor.name} cannot perform a ranged attack on {target.name} due to incorrect distance (distance: {distance}).")


class Parry(Action):
    cooldown_duration = 2  # クールタイムの初期値(何ターン後に使えるか)
    cost = 15  # パリィのコスト

    def __init__(self, actor, controller):
        super().__init__(actor, controller)
        self.is_active = False  # パリィ中かどうか
        self.cooldown_counter = 0  # パリィのクールタイム

    def __call__(self, turn):
        if self.actor.sp >= self.cost and not self.is_active and self.cooldown_counter == 0:
            self.is_active = True
            self.actor.use_sp(self.cost)
            self.cooldown_counter = self.cooldown_duration
            self.controller.log_action(turn, f"{self.actor.name} started parrying!")
        elif self.cooldown_counter > 0:
            self.controller.log_action(turn, f"{self.actor.name}'s parry is on cooldown.")
        else:
            self.controller.log_action(turn, f"{self.actor.name} doesn't have enough SP.")

    def update(self, is_active=False, is_cooldown=False):
        if is_active:
            self.is_active = False
        if is_cooldown:
            assert self.cooldown_counter > 0
            self.cooldown_counter -= 1
        if (not is_active) and (not is_cooldown):
            assert False


class Rest(Action):
    recovery_value = 15

    def __init__(self, actor, controller):
        super().__init__(actor, controller)

    def __call__(self, turn):
        self.actor.recovery_sp(self.recovery_value)
        self.controller.log_action(turn, f"{self.actor.name} rests and recovers {self.recovery_value} SP. Total SP: {self.actor.sp}")


class Trap(Action):
    cost = 15  # 罠設置のコスト
    damage = 25  # 罠のダメージ

    def __init__(self, actor, controller):
        super().__init__(actor, controller)
        self.traps = []  # 設置された罠のリスト

    def __call__(self, direction, turn):
        if self.actor.sp < self.cost:
            self.controller.log_action(turn, f"{self.actor.name} does not have enough SP to set a trap!")
            return

        # 罠を設置する位置を計算
        if direction == "trap_up":
            position = (self.actor.x, max(0, self.actor.y - 1))
        elif direction == "trap_down":
            position = (self.actor.x, min(self.controller.y_max - 1, self.actor.y + 1))
        elif direction == "trap_left":
            position = (max(0, self.actor.x - 1), self.actor.y)
        elif direction == "trap_right":
            position = (min(self.controller.x_max - 1, self.actor.x + 1), self.actor.y)
        else:
            self.controller.log_action(turn, f"{self.actor.name} tried to set a trap in an invalid direction.")
            return

        # 設置先に他のロボットがいないかチェック
        if self.controller.is_position_occupied(*position):
            self.controller.log_action(turn, f"{self.actor.name} tried to set a trap at {position}, but the position is occupied.")
            return

        # 設置先にトラップがないかチェック（自分または相手のトラップ）
        if self.controller.is_trap_at_position(*position):
            self.controller.log_action(turn, f"{self.actor.name} tried to set a trap at {position}, but a trap is already there.")
            return

        # 罠を設置
        self.actor.use_sp(self.cost)
        self.traps.append(position)
        self.controller.log_action(turn, f"{self.actor.name} set a trap at {position}.")

    def check_trap(self, target):
        """敵が罠にかかったかを確認し、ダメージを与える"""
        if target.position in self.traps:
            self.traps.remove(target.position)
            damage = target.receive_attack(self.damage)
            self.controller.log_action(self.controller.turn, f"{target.name} stepped on a trap and took {damage} damage!")


class Steal(Action):
    cost = 10  # スタミナを盗む行動のコスト
    steal_amount = 15  # 奪うスタミナの量

    def __init__(self, actor, controller):
        super().__init__(actor, controller)

    def __call__(self, target, turn):
        if self.actor.sp < self.cost:
            self.controller.log_action(turn, f"{self.actor.name} does not have enough SP to steal!")
            return

        if is_adjacent(self.actor, target):
            if target.sp > 0:
                stolen_sp = min(self.steal_amount, target.sp)
                target.use_sp(stolen_sp)
                self.actor.recovery_sp(stolen_sp)
                self.actor.use_sp(self.cost)
                self.controller.log_action(
                    turn, f"{self.actor.name} steals {stolen_sp} SP from {target.name}.")
            else:
                self.controller.log_action(turn, f"{target.name} has no SP to steal!")
        else:
            self.controller.log_action(turn, f"{self.actor.name} tried to steal from a non-adjacent target.")


class Teleport(Action):
    cost = 20  # テレポートのコスト

    def __init__(self, actor, controller):
        super().__init__(actor, controller)

    def __call__(self, turn):
        if self.actor.sp < self.cost:
            self.controller.log_action(turn, f"{self.actor.name} does not have enough SP to teleport!")
            return

        import random
        # ランダムな位置を生成（フィールド内に収まるように調整）
        new_x = random.randint(0, self.controller.x_max - 1)
        new_y = random.randint(0, self.controller.y_max - 1)

        # 移動先に他のロボットがいないかチェック
        if self.controller.is_position_occupied(new_x, new_y):
            self.controller.log_action(turn, f"{self.actor.name} tried to teleport to ({new_x}, {new_y}), but the position is occupied.")
            return

        # テレポートを実行
        self.actor.use_sp(self.cost)
        self.actor.set_position(new_x, new_y)
        self.controller.log_action(turn, f"{self.actor.name} teleported to ({new_x}, {new_y}).")


class Camouflage(Action):
    cost = 20  # カモフラージュのコスト
    duration = 3  # カモフラージュの持続ターン数

    def __init__(self, actor, controller):
        super().__init__(actor, controller)
        self.is_active = False  # カモフラージュ中かどうか
        self.remaining_turns = 0  # カモフラージュの残りターン数
        self.last_known_position = None  # カモフラージュ開始時の位置を保持

    def __call__(self, turn):
        if self.actor.sp < self.cost:
            self.controller.log_action(turn, f"{self.actor.name} does not have enough SP to activate camouflage!")
            return

        if not self.is_active:
            self.actor.use_sp(self.cost)
            self.is_active = True
            self.remaining_turns = self.duration
            self.last_known_position = self.actor.position  # 現在の位置を記録
            self.controller.log_action(turn, f"{self.actor.name} activates camouflage and hides its position for {self.duration} turns!")
        else:
            self.controller.log_action(turn, f"{self.actor.name} is already camouflaged!")

    def update(self):
        """ターンごとにカモフラージュの状態を更新"""
        if self.is_active:
            self.remaining_turns -= 1
            if self.remaining_turns <= 0:
                self.is_active = False
                self.controller.log_action(self.controller.turn, f"{self.actor.name}'s camouflage has worn off.")


class Scan(Action):
    cost = 10  # スキャンのコスト
    duration = 1  # スキャンの持続ターン数

    def __init__(self, actor, controller):
        super().__init__(actor, controller)
        self.is_active = False  # スキャン中かどうか
        self.remaining_turns = 0  # スキャンの残りターン数

    def __call__(self, turn):
        if self.actor.sp < self.cost:
            self.controller.log_action(turn, f"{self.actor.name} does not have enough SP to scan!")
            return

        self.actor.use_sp(self.cost)
        self.is_active = True
        self.remaining_turns = self.duration

    def update(self):
        """ターンごとにスキャンの状態を更新"""
        if self.is_active:
            self.remaining_turns -= 1
            if self.remaining_turns <= 0:
                self.is_active = False
                self.controller.log_action(self.controller.turn, f"{self.actor.name}'s scan effect has worn off.")


class SuperRest(Action):
    recovery_value = 30  # 通常休息より多く回復

    def __init__(self, actor, controller):
        super().__init__(actor, controller)
        self.is_active = False

    def __call__(self, turn):
        self.actor.recovery_sp(self.recovery_value)
        self.is_active = True  # 攻撃時のダメージ倍率用フラグ
        self.controller.log_action(turn, f"{self.actor.name} super rests and recovers {self.recovery_value} SP. Total SP: {self.actor.sp}")

    def reset(self):
        self.is_active = False
