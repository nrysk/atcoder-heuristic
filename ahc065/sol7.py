"""
N x Nのグリッド上にベルトコンベアを配置し、順番に動かすことで数字を昇順に除去する問題

マスには1個の数字が配置されており、0から1N^2-1までの数字が1枚ずつ存在する。
マスにはベルトコンベアを2重まで配置できる。
ベルトコンベアは環状に配置する必要がある。
搬出口は (0, N/2) に固定されている。

制約
- N = 20
"""

import random
import sys
import time
import itertools
from dataclasses import dataclass


@dataclass(slots=True)
class State:
    board: list[int]
    min_number: int
    score: int
    last_operation: tuple[int, int] | None  # (conveyor_idx, direction)
    prev: "State | None"


def debug_board(
    n: int,
    board: list[int],
) -> None:
    for i in range(0, len(board), n):
        print(
            "\t".join(f"{x:2}" for x in board[i : i + n]), flush=True, file=sys.stderr
        )


def arrange_conveyors(
    n: int,
) -> list[list[tuple[int, int]]]:
    """
    搬出口を通る縦向きのベルトコンベアを1つ配置する。
    縦幅2マスの横向きのベルトコンベアをN/2個配置する。
    シャッフル用のベルトコンベアを2つ配置する。
    全て時計周りを順方向とする。
    """

    # WIDTH = n // 2
    WIDTH = n // 5
    # WIDTH = n // 10
    conveyors = []

    # 縦向きのベルトコンベア
    for start in range(0, n, WIDTH):
        conveyor = []
        for x in range(start, start + WIDTH, 2):
            conveyor.extend((y, x) for y in range(1, n))
            conveyor.extend((y, x + 1) for y in reversed(range(1, n)))
        conveyor.extend((0, x) for x in reversed(range(start, start + WIDTH)))
        conveyors.append(conveyor)

    # 横向きのベルトコンベア
    WIDTH = n // 10
    for start in range(0, n, WIDTH):
        conveyor = []
        for y in range(start, start + WIDTH, 2):
            conveyor.extend((y, x) for x in range(1, n // 2))
            conveyor.extend((y + 1, x) for x in reversed(range(1, n // 2)))
        conveyor.extend((y, 0) for y in reversed(range(start, start + WIDTH)))
        conveyors.append(conveyor)

    for start in range(0, n, WIDTH):
        conveyor = []
        for y in range(start, start + WIDTH, 2):
            conveyor.extend((y, x) for x in range(n // 2 + 1, n))
            conveyor.extend((y + 1, x) for x in reversed(range(n // 2 + 1, n)))
        conveyor.extend((y, n // 2) for y in reversed(range(start, start + WIDTH)))
        conveyors.append(conveyor)

    return conveyors


def rotate_conveyors(
    conveyors: list[list[tuple[int, int]]],
    conveyor_idx: int,
    n: int,
    board: list[int],
    steps: int,
) -> list[tuple[int, int]]:
    """
    ベルトコンベアを回転させる。
    """

    if steps == 0:
        return []

    conveyor = conveyors[conveyor_idx]
    length = len(conveyor)

    vals = [board[y * n + x] for y, x in conveyor]

    shift = steps % length
    rotated_vals = vals[-shift:] + vals[:-shift]

    for (y, x), val in zip(conveyor, rotated_vals):
        board[y * n + x] = val

    direction = 1 if steps > 0 else -1
    return [(conveyor_idx, direction) for _ in range(abs(steps))]


def get_number_position(
    n: int,
    board: list[int],
    number: int,
) -> tuple[int, int]:
    """
    数字の位置を取得する。
    """

    idx = board.index(number)
    return divmod(idx, n)


def evaluate(
    n: int,
    board: list[int],
    min_number: int,
) -> int:
    """評価関数"""
    score = 0
    score += (n * n - min_number) * 10000000000
    for idx in range(n * n):
        y, x = divmod(idx, n)

        if board[idx] == -1:
            continue
        elif board[idx] == min_number:
            score += 100 * (n * n - board[idx]) * (abs(y - 0) + abs(x - n // 2))
        else:
            score += (n * n - board[idx]) * (abs(y - 0) + abs(x - n // 2))

    return score


def restore_operations(
    state: State,
) -> list[tuple[int, int]]:
    operations = []
    while state.prev is not None:
        operations.append(state.last_operation)
        state = state.prev
    return list(reversed(operations))


def solve(
    n: int,
    a: list[list[int]],
) -> tuple[list[list[tuple[int, int]]], list[tuple[int, int]]]:
    BEAM_WIDTH = 3

    board = list([x for row in a for x in row])
    conveyors = arrange_conveyors(n)

    min_number = 0
    if board[n // 2] == 0:
        board[n // 2] = -1
        min_number = 1

    beam = [
        State(
            board=board,
            min_number=min_number,
            score=evaluate(n, board, min_number),
            last_operation=None,
            prev=None,
        )
    ]

    for _ in range(5000):
        next_beam = []

        for state in beam:
            for conveyor_idx in range(len(conveyors)):
                for direction in [-1, 1]:
                    if state.last_operation is not None and (
                        conveyor_idx == state.last_operation[0]
                        and direction == -state.last_operation[1]
                    ):
                        continue

                    new_board = list(state.board)
                    rotate_conveyors(conveyors, conveyor_idx, n, new_board, direction)
                    min_number = state.min_number

                    if new_board[n // 2] == state.min_number:
                        new_board[n // 2] = -1
                        min_number = state.min_number + 1

                    next_state = State(
                        board=new_board,
                        min_number=min_number,
                        score=evaluate(n, new_board, min_number),
                        last_operation=(conveyor_idx, direction),
                        prev=state,
                    )
                    if next_state.min_number == n * n:
                        return conveyors, restore_operations(next_state)

                    next_beam.append(next_state)

        next_beam.sort(
            key=lambda s: s.score,
        )
        beam = next_beam[:BEAM_WIDTH]
        print(beam[0].score, beam[0].min_number, file=sys.stderr)

    return conveyors, restore_operations(beam[0])


def main():

    n = int(input())
    a = [list(map(int, input().split())) for _ in range(n)]

    best_result = solve(n, a)

    # 出力
    print(len(best_result[0]))
    for conveyor in best_result[0]:
        print(len(conveyor), " ".join(f"{x} {y}" for x, y in conveyor))

    print(len(best_result[1]))
    for conveyor_idx, direction in best_result[1]:
        print(conveyor_idx, direction)


if __name__ == "__main__":
    main()
