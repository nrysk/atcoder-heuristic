"""
N x Nのグリッド上に配置された全ての段ボール箱を (0, 0) に運び出すヒューリスティック問題
段ボールは重ねる事ができ、重ねた段ボールの重さに依って下の段ボールの耐久力が減少する
耐久力は移動する度に減少する

操作：
- 1: 現在地の段ボールをスタックに積む
- 2: スタックの段ボールを現在地に置く
- U,D,L,R: 現在地から上下左右のいずれかに移動する
"""

import sys
import random
from dataclasses import dataclass

MANHATTAN_DISTANCE = []
EUCLID_DISTANCE = []


def init_manhattan_distance(n: int):
    global MANHATTAN_DISTANCE, EUCLID_DISTANCE
    MANHATTAN_DISTANCE = [0] * (n * n)
    EUCLID_DISTANCE = [0] * (n * n)
    for i in range(1, n * n):
        MANHATTAN_DISTANCE[i] = (i // n) + (i % n)
        EUCLID_DISTANCE[i] = ((i // n) ** 2 + (i % n) ** 2) ** 0.5


@dataclass
class State:
    current_idx: int
    stack: tuple[int, ...]
    current_loads: tuple[int, ...]  # 現時点までにstack[i]の段ボールに与えられた負荷
    operations: tuple[str, ...]
    score: int


def move(
    n: int,
    current_idx: int,
    target_idx: int,
    operations: list[str],
) -> int:
    current_y, current_x = divmod(current_idx, n)
    target_y, target_x = divmod(target_idx, n)

    if current_y < target_y:
        operations.extend(["D"] * (target_y - current_y))
    else:
        operations.extend(["U"] * (current_y - target_y))

    if current_x < target_x:
        operations.extend(["R"] * (target_x - current_x))
    else:
        operations.extend(["L"] * (current_x - target_x))

    return target_idx


def next_loads(
    weights: list[int],
    current_loads: tuple[int, ...],
    stack: tuple[int, ...],
):
    w = 0
    loads = list(current_loads)
    for i in reversed(range(len(stack))):
        loads[i] += w
        w += weights[stack[i]]
    return tuple(loads)


def can_return_if_loaded(
    n: int,
    weights: list[int],
    durabilities: list[int],
    current_idx: int,
    stack: tuple[int, ...],
    loads: tuple[int, ...],
) -> bool:
    # 現在のスタックの段ボールを持って (0, 0) に帰れるか
    dist = MANHATTAN_DISTANCE[current_idx]
    w = weights[current_idx]
    for idx, load in zip(reversed(stack), reversed(loads)):
        if durabilities[idx] <= w * dist + load:
            return False
        w += weights[idx]
    return True


def evaluate(
    n: int,
    stack: list[int],
):
    # スタックに積まれた段ボールが遠くのものであるほど良い
    # return sum(MANHATTAN_DISTANCE[idx] for idx in stack)
    return sum(EUCLID_DISTANCE[idx] for idx in stack)


def one_path(
    n: int,
    weights: list[int],
    durabilities: list[int],
    board: set[int],
    target_idx: int,
) -> tuple[list[str], list[int]]:
    operations = []

    # target_idx の段ボールを積む
    move(n, 0, target_idx, operations)
    operations.append("1")

    # ビームサーチで (0, 0) に戻る経路を探索する
    # アクション：上か左に移動
    # アクション後：可能ならば段ボールを積む

    BEAM_WIDTH = 100

    beam = [
        State(
            current_idx=target_idx,
            stack=(target_idx,),
            current_loads=(0,),
            operations=(),
            score=evaluate(n, [target_idx]),
        )
    ]

    max_step = MANHATTAN_DISTANCE[target_idx]
    for _ in range(max_step):
        new_beam = []
        for state in beam:
            current_y, current_x = divmod(state.current_idx, n)
            next_moves = []
            if current_y > 0:
                next_moves.append((state.current_idx - n, "U"))
            if current_x > 0:
                next_moves.append((state.current_idx - 1, "L"))

            for next_idx, move_op in next_moves:
                new_operations = state.operations + (move_op,)
                new_loads = next_loads(weights, state.current_loads, state.stack)
                new_stack = state.stack

                # 現在地の段ボールを積んで (0, 0) に帰れるならば積む
                if next_idx in board and can_return_if_loaded(
                    n, weights, durabilities, next_idx, state.stack, new_loads
                ):
                    new_operations += ("1",)
                    new_stack = state.stack + (next_idx,)
                    new_loads += (0,)

                new_beam.append(
                    State(
                        current_idx=next_idx,
                        stack=new_stack,
                        current_loads=new_loads,
                        operations=new_operations,
                        score=evaluate(n, new_stack),
                    )
                )

        new_beam.sort(key=lambda s: s.score, reverse=True)
        beam = new_beam[:BEAM_WIDTH]

    return operations + list(beam[0].operations), beam[0].stack


def solve(
    n: int,
    w: list[list[int]],
    d: list[list[int]],
) -> list[str]:
    """
    1. 段ボールが存在するランダムなセルを選択する
    2. そこに行き、段ボールをスタックに積む
    3. 上か左に移動して、可能ならば段ボールをスタックに積む
    4. (0, 0) に戻る経路はビームサーチで探索して決定する
    """

    operations = []

    board = set([i for i in range(1, n * n)])
    weights = [weight for row in w for weight in row]
    durabilities = [durability for row in d for durability in row]
    order = list(range(1, n * n))
    order.sort(key=lambda idx: EUCLID_DISTANCE[idx], reverse=True)

    for target_idx in order:
        if target_idx not in board:
            continue
        path_operations, stack = one_path(n, weights, durabilities, board, target_idx)
        operations.extend(path_operations)
        for idx in stack:
            board.remove(idx)

    return operations


def main():
    n = int(input())
    w = [list(map(int, input().split())) for _ in range(n)]
    d = [list(map(int, input().split())) for _ in range(n)]

    init_manhattan_distance(n)

    operations = solve(n, w, d)

    print("\n".join(operations))


if __name__ == "__main__":
    main()
