"""
スタックを使って列車の車両入替を行うヒューリスティック問題

R個のレーンに10両の車両が入っており、車両は0から10R-1の番号がついている
対応するレーンに昇順になるように車両を入れ替える
より正しい順番で少ない回数で入れ替えるほどスコアが高い
スタックが交差しない限り、同じターンに車両の入れ替えが可能
R個のスタックが2組あり、互いに向かい合っている

ルールと制約：
- R=10
- 最大4000ターン
"""

from dataclasses import dataclass


@dataclass
class MoveType:
    move_type: int  # 移動種類 (0: 出発線から待避線, 1: 待避線から出発線)
    from_lane_index: int  # 移動元レーン
    to_lane_index: int  # 移動先レーン
    num_cars: int  # 移動車両数


@dataclass
class Move:
    k: int  # 同時移動数
    types: list[MoveType]


@dataclass
class SolveResult:
    t: int  # 使用ターン数
    moves: list[Move]  # 各ターンの移動内容


# フェーズ1： 下一桁を見て同じ待避線に移動させる ex) 0, 10, 20, ...はレーン0へ、1, 11, 21, ...はレーン1へ
# フェーズ2: レーン0から順番に正しい出発線に移動させる ex) 00はレーン0からレーン0へ、10はレーン0からレーン1へ、01はレーン1からレーン0へ、11はレーン1からレーン1へ
# 同時移動は考慮せず、単純に1台ずつ移動させる
def solve1(
    r: int,
    y: list[list[int]],
) -> SolveResult:

    depature_lanes = [list(lane) for lane in y]  # 出発線
    waiting_lanes = [[] for _ in range(r)]  # 待避線
    moves = []

    # フェーズ1
    for i in range(r):
        for car in reversed(depature_lanes[i]):
            waiting_lane_index = car % 10
            waiting_lanes[waiting_lane_index].append(car)
            moves.append(Move(k=1, types=[(0, i, waiting_lane_index, 1)]))

    # フェーズ2
    for i in range(r):
        for car in reversed(waiting_lanes[i]):
            depature_lanes_index = car // 10
            moves.append(Move(k=1, types=[(1, depature_lanes_index, i, 1)]))

    return SolveResult(t=len(moves), moves=moves)


def find_most_cars_lane(lanes: list[list[int]]) -> int:
    max_cars = 0
    max_lane_index = 0
    for i, lane in enumerate(lanes):
        if len(lane) > max_cars:
            max_cars = len(lane)
            max_lane_index = i
    return max_lane_index


def lanes_are_empty(lanes: list[list[int]]) -> bool:
    return all(len(lane) == 0 for lane in lanes)


def depature_to_waiting(
    from_index: int,
    depature_lanes: list[list[int]],
    to_index: int,
    waiting_lanes: list[list[int]],
    num_cars: int,
) -> MoveType:
    for _ in range(num_cars):
        car = depature_lanes[from_index].pop()
        waiting_lanes[to_index].append(car)
    return MoveType(
        move_type=0,
        from_lane_index=from_index,
        to_lane_index=to_index,
        num_cars=num_cars,
    )


def waiting_to_depature(
    from_index: int,
    waiting_lanes: list[list[int]],
    to_index: int,
    depature_lanes: list[list[int]],
    num_cars: int,
) -> MoveType:
    for _ in range(num_cars):
        car = waiting_lanes[from_index].pop()
        depature_lanes[to_index].append(car)
    # ここのto_indexとfrom_indexは逆になることに注意
    return MoveType(
        move_type=1,
        from_lane_index=to_index,
        to_lane_index=from_index,
        num_cars=num_cars,
    )


def count_same_waiting_lane_cars(
    lane: list[int],
) -> tuple[int, int]:  # (num_cars, waiting_lane_index)
    if not lane:
        return 0, -1
    waiting_lane_index = lane[-1] % 10
    num_cars = 0
    for car in reversed(lane):
        if car % 10 == waiting_lane_index:
            num_cars += 1
        else:
            break
    return num_cars, waiting_lane_index


# solve1を改良し、一括移動や同時移動を取り入れる
def solve2(
    r: int,
    y: list[list[int]],
) -> SolveResult:
    NUM_CARS_PER_LANE = 10

    depature_lanes = [list(lane) for lane in y]  # 出発線
    waiting_lanes = [[] for _ in range(r)]  # 待避線
    moves = []

    # フェーズ1
    while not lanes_are_empty(depature_lanes):
        move_types = []
        last_waiting_lane_index = -1

        for i in range(r):
            # 出発線が空ならスキップ
            if not depature_lanes[i]:
                continue

            num_cars_to_move, waiting_lane_index = count_same_waiting_lane_cars(
                depature_lanes[i]
            )

            # 交差確認（iは昇順なので、last_waiting_lane_index < waiting_lane_indexなら交差しない）
            if waiting_lane_index > last_waiting_lane_index:
                last_waiting_lane_index = waiting_lane_index
                move_type = depature_to_waiting(
                    from_index=i,
                    depature_lanes=depature_lanes,
                    to_index=waiting_lane_index,
                    waiting_lanes=waiting_lanes,
                    num_cars=num_cars_to_move,
                )

                move_types.append(move_type)

        if move_types:
            moves.append(Move(k=len(move_types), types=move_types))

    # フェーズ2
    for i in range(r):
        for car in reversed(waiting_lanes[i]):
            depature_lanes_index = car // 10
            moves.append(
                Move(
                    k=1,
                    types=[
                        MoveType(
                            move_type=1,
                            from_lane_index=depature_lanes_index,
                            to_lane_index=i,
                            num_cars=1,
                        )
                    ],
                )
            )

    return SolveResult(t=len(moves), moves=moves)


def main():
    r = int(input())
    y = [
        list(map(int, input().split())) for _ in range(r)
    ]  # y[i][j]はi番目のレーンのj番目の車両の番号

    res = solve2(r, y)

    print(res.t)
    for move in res.moves:
        print(move.k)
        for move_type in move.types:
            print(
                move_type.move_type,
                move_type.from_lane_index,
                move_type.to_lane_index,
                move_type.num_cars,
            )


if __name__ == "__main__":
    main()
