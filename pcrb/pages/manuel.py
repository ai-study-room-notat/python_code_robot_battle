import streamlit as st
from pcrb.constants import PLAYER_ROBOT_NAME, ENEMY_ROBOT_NAME

DOCUMENT = '''
# ゲーム説明書

## 概要
このゲームでは、プレイヤーがプログラムで定義したロジックを使ってロボットを操作します。他のロボットとの対戦を通じて、戦略的な判断力を試すことができます。

## ゲームの目的
- 自分のロボットを操作して、敵ロボットを倒すこと。
- ロボットの行動を計画し、効率的にエネルギーを使いながら勝利を目指しましょう。

## 基本ルール
1. **ロボットの初期状態**
    - HP (体力): 100
    - SP (エネルギー): 50
    - 攻撃力: 20
4. **勝敗条件**
    - 相手ロボットのHPを0にすることで勝利。
    - 自分のロボットのHPが0になると敗北。

## ロボットロジックの作成
プレイヤーは以下の関数を実装することで、自分のロボットの動きを定義します。

### 関数定義

```python
def robot_logic(robot, game_info, memos):
    # ロジックを記述
    pass
```

- **引数**:
  - `robot`: 自分のロボットを操作するオブジェクト。
  - `game_info`: 敵ロボットの位置やゲームの状態を表す辞書。
  - `memos`: 前ターンの情報を保持する辞書。
- **戻り値**:
  - ロボットの行動を指示するコマンド（例: `"attack"`, `"rest"`）。

### 関数内で利用できるライブラリ

- `random`: ランダムな動きを生成するために使用できます。
- `math`: 数学的な計算を行うために使用できます。

## ゲームの進め方
1. **ロジックの実装**
    - `robot_logic` 関数を作成し、ロボットの行動を決定します。
2. **ゲームの開始**
    - 実装したロジックをゲームに読み込んで、対戦を開始します。
3. **結果の確認**
    - 各ターンのログを通じて戦況を確認し、戦略を改善します。

## 注意事項
- **エネルギー管理**: 無駄な行動を避け、効率的に攻撃や防御を行いましょう。
- **敵の動きの予測**: 適切に対応するロジックを作成することが勝利の鍵です。

# アクション一覧

## 1. 通常攻撃 (Attack)
- **効果**: 隣接する敵に攻撃を行い、20ダメージを与える。
- **コスト**: SP 10
- **条件**: 敵が隣接している必要があります。
- **特殊効果**: 敵がパリィ中の場合、自分が1ターンスタンします。
- **robot_logic の返却値**: `'attack'`

## 2. 移動 (Move)
- **効果**: 指定した方向に1マス移動します。
- **コスト**: SP 5
- **条件**: 移動先に他のロボットがいないこと。
- **robot_logic の返却値**: `'up'`, `'down'`, `'left'`, `'right'`

## 3. 防御 (Defend)
- **効果**: 防御モードを有効にし、次のターンまでのダメージを50%軽減します。
- **コスト**: SP 10
- **持続時間**: 1ターン
- **robot_logic の返却値**: `'defend'`

## 4. 遠隔攻撃 (RangedAttack)
- **効果**: 2マス離れた敵に15ダメージを与える。
- **コスト**: SP 15
- **条件**: 敵との距離がちょうど2マスであること。
- **robot_logic の返却値**: `'ranged_attack'`

## 5. パリィ (Parry)
- **効果**: パリィモードを有効にし、敵の攻撃を無効化します。
- **コスト**: SP 15
- **クールタイム**: 2ターン
- **特殊効果**: パリィ成功時、敵を1ターンスタンさせます。
- **robot_logic の返却値**: `'parry'`

## 6. 休息 (Rest)
- **効果**: SPを15回復します。
- **コスト**: なし
- **robot_logic の返却値**: `'rest'`

## 7. 罠設置 (Trap)
- **効果**: 指定した方向に罠を設置します。敵が罠にかかると25ダメージを与えます。
- **コスト**: SP 15
- **条件**: 設置先に他のロボットや罠がないこと。
- **robot_logic の返却値**: `'trap_up'`, `'trap_down'`, `'trap_left'`, `'trap_right'`

## 8. スタミナ盗み (Steal)
- **効果**: 隣接する敵から最大15SPを奪い、自分のSPを回復します。
- **コスト**: SP 10
- **条件**: 敵が隣接していること。
- **robot_logic の返却値**: `'steal'`

## 9. テレポート (Teleport)
- **効果**: ランダムな位置に瞬間移動します。
- **コスト**: SP 20
- **条件**: 移動先に他のロボットがいないこと。
- **robot_logic の返却値**: `'teleport'`

## 10. カモフラージュ (Camouflage)
- **効果**: 自分の位置を隠し、敵から見えなくなります。
- **コスト**: SP 20
- **持続時間**: 3ターン
- **robot_logic の返却値**: `'camouflage'`

## 11. スキャン (Scan)
- **効果**: 敵のSPや罠の位置を確認します。
- **コスト**: SP 10
- **持続時間**: 1ターン
- **robot_logic の返却値**: `'scan'`

# ログ情報

## ログのフォーマット

- ログは以下の形式で記録されます。

```json
[
    {
        "settings": {
            "max_turn": 100,
            "x_max": 9,
            "y_max": 7
        }
    },
    {
        "turn": 0,
        "robots": [
            {
                "name": "Robot A",
                "position": [
                    1,
                    3
                ],
                "hp": 100,
                "sp": 50,
                "defense_mode": false
            },
            {
                "name": "Robot B",
                "position": [
                    7,
                    3
                ],
                "hp": 100,
                "sp": 50,
                "defense_mode": false
            }
        ],
        "action": {
            "robot_name": null,
            "action": null
        }
    },
    {
        "turn": 1,
        "robots": [
            {
                "name": "Robot A",
                "position": [
                    1,
                    3
                ],
                "hp": 100,
                "sp": 50,
                "defense_mode": false
            },
            {
                "name": "Robot B",
                "position": [
                    6,
                    3
                ],
                "hp": 100,
                "sp": 45,
                "defense_mode": false
            }
        ],
        "action": {
            "robot_name": "Robot B",
            "action": "left"
        }
    },
```

## ログの説明

- `settings`: ゲームの設定情報（最大ターン数、ボードのサイズなど）。
- `turn`: 現在のターン数。
- `robots`: 各ロボットの情報（名前、位置、HP、SP、防御モードの状態）。
- `action`: 現在のターンでのロボットの行動（どのロボットがどのアクションを実行したか）。

'''


def main():
    # ページタイトル
    st.title("Manuel")
    st.markdown(DOCUMENT)


if __name__ == '__main__':
    main()