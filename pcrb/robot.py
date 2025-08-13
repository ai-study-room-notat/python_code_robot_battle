from actions import Attack
from actions import Move
from actions import Defend
from actions import RangedAttack
from actions import Parry
from actions import Rest
from actions import Trap
from actions import Steal
from actions import Teleport
from actions import Camouflage
from actions import Scan
from actions import SuperRest


class Robot:
    def __init__(self, name, x, y, robot_logic_function, controller):
        self._name = name
        self._x = x
        self._y = y
        self._hp = 100
        self._sp = 50
        self._stun_counter = 0  # ロボットがスタンしている時間

        self.attack = Attack(self, controller)
        self.move = Move(self, controller)
        self.defend = Defend(self, controller)
        self.ranged_attack = RangedAttack(self, controller)
        self.parry = Parry(self, controller)
        self.rest = Rest(self, controller)
        self.trap = Trap(self, controller)
        self.steal = Steal(self, controller)
        self.teleport = Teleport(self, controller)
        self.camouflage = Camouflage(self, controller)
        self.scan = Scan(self, controller)
        self.super_rest = SuperRest(self, controller)

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

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    # @property
    # def defense_mode(self):
    #     return self._defense_mode

    @property
    def stun_counter(self):
        return self._stun_counter

    def receive_attack(self, damage):
        """攻撃を受ける
        :param damage: 攻撃のダメージ量
        """
        if self.super_rest.is_active:
            damage *= 1.5  # 超休息直後はダメージ1.5倍
            self.super_rest.reset()  # 攻撃されたらフラグ解除
        if self.defend.is_active:
            damage *= self.defend.reduction
        self._hp -= max(damage, 0)
        if self._hp <= 0:
            print(f"{self._name} has been destroyed!")
        return damage

    def use_sp(self, amount):
        """SPを消費するメソッド。"""
        if self._sp >= amount:
            self._sp -= amount
        else:
            assert False

    def recovery_sp(self, amount):
        """SPを回復するメソッド。"""
        self._sp += amount

    def is_parrying(self):
        return self.parry.is_active

    def set_position(self, new_x, new_y):
        self._x, self._y = new_x, new_y

    def start_turn(self):
        """ターン開始時にロボットの状態を更新"""
        self.stun_update()
        self.super_rest.reset()  # 超休息効果をターン開始時に解除

        if self.defend.is_active:
            print(f"{self._name} ends defense mode.")
            self.defend.update()

        if self.parry.is_active:
            print(f"{self._name} ends parry mode.")
            self.parry.update(is_active=True)

        if self.parry.cooldown_counter > 0:
            self.parry.update(is_cooldown=True)

        if self.camouflage.is_active:
            self.camouflage.update()

        if self.scan.is_active:
            self.scan.update()

    def stun(self, duration):
        """ロボットをスタン状態にする
        :param duration: スタンの持続時間
        """
        self._stun_counter = duration
        print(f"{self._name} was stunned.")
    
    def stun_update(self):
        """スタン状態の更新"""
        if self._stun_counter > 0:
            self._stun_counter -= 1
            print(f"{self._name} is stunned. (duration={self._stun_counter})")
            if self._stun_counter == 0:
                print(f"{self._name} is no longer stunned.")
        else:
            print(f"{self._name} is not stunned.")

    def is_alive(self):
        return self._hp > 0

    def status(self):
        print(f"{self._name}: HP={self._hp}, SP={self._sp}, Position=({self._x}, {self._y})")

    def reset(self, x: int, y: int):
        """
        * 位置を (x, y) に戻す  
        * HP / SP / スタンなどの数値を初期値へ  
        * 各アクションオブジェクトのフラグやクールダウンを初期化
        """
        # 位置
        self._x, self._y = x, y

        # 基本ステータス
        self._hp = 100
        self._sp = 50
        self._stun_counter = 0

        # アクション系フラグをリセット
        self.defend.is_active      = False
        self.parry.is_active       = False
        self.parry.cooldown_counter = 0
        self.camouflage.is_active  = False
        self.scan.is_active        = False

        # 罠を全消去
        self.trap.traps.clear()

        # 各アクションに reset() があれば呼ぶ（クールダウンなどを内包）
        for ability in [
            self.attack, self.move, self.defend, self.ranged_attack,
            self.parry, self.rest, self.trap, self.steal, self.teleport,
            self.camouflage, self.scan,
        ]:
            if hasattr(ability, "reset") and callable(ability.reset):
                ability.reset()

        print(f"[RESET] {self._name} is back to ({x}, {y})  HP=100  SP=50")