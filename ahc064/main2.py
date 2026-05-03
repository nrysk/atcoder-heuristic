"""
スタックを使って列車の車両入替を行うヒューリスティック問題

R個のレーンに10両の車両が入っており、車両は0から10R-1の番号がついている
対応するレーンに昇順になるように車両を入れ替える
より正しい順番で少ない回数で入れ替えるほどスコアが高い
スタックが交差しない限り、同じターンに車両の入れ替えが可能
R個のスタックが2組あり、互いに向かい合っている
出発線の先頭は配列の先頭だが、待機線の先頭は配列の末尾であることに注意

ルールと制約：
- R=10
- 最大4000ターン
"""

from typing import NamedTuple
import random


class Move(NamedTuple):
    move_type: int  # 移動種類 (0: 出発線から待避線, 1: 待避線から出発線)
    depature_lane_index: int  # 出発線側のレーン番号
    waiting_lane_index: int  # 待避線側のレーン番号
    num_cars: int  # 移動車両数


class MoveStep(NamedTuple):
    k: int  # 同時移動数
    moves: list[Move]  # 各移動の内容


class SolveResult(NamedTuple):
    t: int  # 使用ターン数
    move_steps: list[MoveStep]  # 各ターンの移動内容


def lanes_are_empty(lanes: list[list[int]]) -> bool:

    return all(len(lane) == 0 for lane in lanes)


def move_cars(
    depature_lanes: list[list[int]],
    depature_lane_index: int,
    waiting_lanes: list[list[int]],
    waiting_lane_index: int,
    num_cars: int,
    move_type: int,
) -> Move:
    """
    車両を移動させる関数
    move_type: 0なら出発線から待避線へ、1なら待避線から出発線へ
    """
    if move_type == 0:
        # 出発線から待避線へ移動
        for _ in range(num_cars):
            car = depature_lanes[depature_lane_index].pop()
            waiting_lanes[waiting_lane_index].append(car)
    else:
        # 待避線から出発線へ移動
        for _ in range(num_cars):
            car = waiting_lanes[waiting_lane_index].pop()
            depature_lanes[depature_lane_index].append(car)

    return Move(move_type, depature_lane_index, waiting_lane_index, num_cars)


def calc_best_move_step_in_phase1(
    r: int,
    depature_lanes: list[list[int]],
    waiting_lanes: list[list[int]],
    # reversed: bool = False,
) -> MoveStep:
    """
    Phase 1: 出発線のトップを見て、対応する待避線に移動させる。
    ex) 車両番号 4はレーン0かレーン1へ、車両番号 15はレーン0かレーン1へ、車両番号 20はレーン2かレーン3へ
    reversed: 出発線9から0の順で見ていくか、0から9の順で見ていくか
    """
    moves = []
    last_waiting_lane_index = -1
    for i in range(r):
        # レーンiが空ならスキップ
        if not depature_lanes[i]:
            continue

        # まとめて移動する車両数をカウント
        waiting_lane_index = depature_lanes[i][-1] // 20 * 2
        num_cars = 0
        for car in reversed(depature_lanes[i]):
            if car // 20 * 2 == waiting_lane_index:
                num_cars += 1
            else:
                break

        # 既に決定した移動と交差せずに移動可能なら、移動内容を追加
        if waiting_lane_index < last_waiting_lane_index:
            continue
        elif waiting_lane_index == last_waiting_lane_index:
            moves.append(
                move_cars(
                    depature_lanes,
                    i,
                    waiting_lanes,
                    waiting_lane_index + 1,
                    num_cars,
                    move_type=0,
                )
            )
            last_waiting_lane_index += 1
        else:
            moves.append(
                move_cars(
                    depature_lanes,
                    i,
                    waiting_lanes,
                    waiting_lane_index,
                    num_cars,
                    move_type=0,
                )
            )
            last_waiting_lane_index = waiting_lane_index

    return MoveStep(k=len(moves), moves=moves)


def is_continuous(car1: int, car2: int) -> bool:
    """
    車両番号 car1 と car2 が連続しているかを判定する関数
    例: 9と10は連続、19と20は連続、19と20は非連続
    """
    return car1 % 10 != 9 and car1 + 1 == car2


def evaluate_state(
    group_index: int,
    depature_lanes: list[list[int]],
    waiting_lanes: list[list[int]],
) -> int:
    """
    - 出発線の先頭に car//10 があれば +1
    - 出発線が空でも待機線の先頭に car//10 == group_index + i があれば +0.75
    - 昇順に車両が並んでいる数だけ +1 (待機線から出発線、レーン番号にかかわらず)
    - 出発線の最後尾と待機線の先頭が連続する番号なら +0.5
    """

    score = 0
    for i in range(2):
        # 出発線の先頭に car//10 があれば +
        if depature_lanes[group_index + i]:
            if (
                depature_lanes[group_index + i][0] // 10 == group_index + i
                and depature_lanes[group_index + i][0] % 10 == 0
            ):
                score += 1
        # 出発線が空でも待機線の先頭に car%10 == 0 があれば +0.75
        else:
            if not waiting_lanes[group_index + i]:
                continue
            target_lane_index = waiting_lanes[group_index + i][-1] // 10
            if waiting_lanes[group_index + i][-1] % 10 == 0:
                if depature_lanes[target_lane_index]:
                    score += 0.25
                else:
                    score += 0.5

        # 昇順に車両が並んでいる数だけ +1 (待機線から出発線、レーン番号にかかわらず)
        for j in range(len(depature_lanes[group_index + i]) - 1):
            if is_continuous(
                depature_lanes[group_index + i][j],
                depature_lanes[group_index + i][j + 1],
            ):
                score += 1
        for j in range(len(waiting_lanes[group_index + i]) - 1):
            if is_continuous(
                waiting_lanes[group_index + i][j + 1], waiting_lanes[group_index + i][j]
            ):
                score += 1

        # 出発線が空ならスキップ
        if not depature_lanes[group_index + i]:
            continue
        for j in range(2):
            # 待機線が空ならスキップ
            if not waiting_lanes[group_index + j]:
                continue
            # 出発線の最後尾と待機線の先頭が連続する番号なら +0.5
            if is_continuous(
                depature_lanes[group_index + i][-1], waiting_lanes[group_index + j][-1]
            ):
                score += 0.5
    return score


def calc_best_move_in_phase2(
    group_index: int,  # グループ先頭のレーン番号 ex) 0, 2, 4, 6, 8
    depature_lanes: list[list[int]],
    waiting_lanes: list[list[int]],
) -> Move | None:
    """
    指定されたグループにおける最適な移動を計算する関数
    1. 可能な移動を全てループする
    2. 各移動後の状態を評価する
    3. 最も評価の高い移動を選択する
    """

    DEPATURE_LANE_CAR_LIMIT = 15
    WAITING_LANE_CAR_LIMIT = 20

    # 可能な線の組み合わせを全てループする
    best_moves = []
    best_score = evaluate_state(group_index, depature_lanes, waiting_lanes) - 1e-9

    for depature_lane_index in range(group_index, group_index + 2):
        for waiting_lane_index in range(group_index, group_index + 2):
            # 出発線から待避線への移動を評価
            for num_cars in range(1, len(depature_lanes[depature_lane_index]) + 1):
                if (
                    len(waiting_lanes[waiting_lane_index]) + num_cars
                    > WAITING_LANE_CAR_LIMIT
                ):
                    continue
                move = move_cars(
                    depature_lanes,
                    depature_lane_index,
                    waiting_lanes,
                    waiting_lane_index,
                    num_cars,
                    move_type=0,
                )
                score = evaluate_state(group_index, depature_lanes, waiting_lanes)
                if score == best_score:
                    best_moves.append(move)
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                # 状態を元に戻す
                move_cars(
                    depature_lanes,
                    depature_lane_index,
                    waiting_lanes,
                    waiting_lane_index,
                    num_cars,
                    move_type=1,
                )

            # 待避線から出発線への移動を評価
            for num_cars in range(1, len(waiting_lanes[waiting_lane_index]) + 1):
                if (
                    len(depature_lanes[depature_lane_index]) + num_cars
                    > DEPATURE_LANE_CAR_LIMIT
                ):
                    continue
                move = move_cars(
                    depature_lanes,
                    depature_lane_index,
                    waiting_lanes,
                    waiting_lane_index,
                    num_cars,
                    move_type=1,
                )
                score = evaluate_state(group_index, depature_lanes, waiting_lanes)
                if score == best_score:
                    best_moves.append(move)
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                # 状態を元に戻す
                move_cars(
                    depature_lanes,
                    depature_lane_index,
                    waiting_lanes,
                    waiting_lane_index,
                    num_cars,
                    move_type=0,
                )

    # 並行移動するパターンも考慮する(出発線0と待避線0、出発線1と待避線1を同時に移動する)

    if best_moves:
        best_move = random.choice(best_moves)
        move_cars(
            depature_lanes,
            best_move.depature_lane_index,
            waiting_lanes,
            best_move.waiting_lane_index,
            best_move.num_cars,
            best_move.move_type,
        )
    return best_move if best_moves else None


def calc_best_move_step_in_phase2(
    r: int,
    depature_lanes: list[list[int]],
    waiting_lanes: list[list[int]],
) -> MoveStep:
    """
    Phase 2: 2レーンずつ正しい順序に並び替える。これにより r/2 並列で移動可能
    """
    moves = []
    for group_index in range(0, r, 2):
        move = calc_best_move_in_phase2(group_index, depature_lanes, waiting_lanes)
        if move is not None:
            moves.append(move)

    return MoveStep(k=len(moves), moves=moves)


def solve(
    r: int,
    y: list[list[int]],
) -> SolveResult:
    """
    r: レーン数
    y: 出発線の車両配置 (y[i][j]はi番目のレーンのj番目の車両番号)

    方針：
    1. 車両番号で20ごとに待避線にまとめる。ex) 車両番号 0~19はレーン0かレーン1へ、20~39はレーン2かレーン3へ
    2. 2レーンずつ正しい順序に並び替える。これにより r/2 並列で移動可能
    """

    move_steps = []

    waiting_lanes = [[] for _ in range(r)]  # 待避線
    while not lanes_are_empty(y):
        move_step = calc_best_move_step_in_phase1(r, y, waiting_lanes)
        if move_step.k == 0:
            break
        move_steps.append(move_step)

    while True:
        move_step = calc_best_move_step_in_phase2(r, y, waiting_lanes)
        if move_step.k == 0:
            break
        move_steps.append(move_step)

    return SolveResult(t=len(move_steps), move_steps=move_steps)


def main():
    r = int(input().strip())
    y = [list(map(int, input().split())) for _ in range(r)]

    result = solve(r, y)

    print(result.t)
    for move_step in result.move_steps:
        print(move_step.k)
        for move in move_step.moves:
            print(
                move.move_type,
                move.depature_lane_index,
                move.waiting_lane_index,
                move.num_cars,
            )


if __name__ == "__main__":
    main()
