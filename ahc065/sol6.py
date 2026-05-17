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
    NUM_SAMPLES = 6
    score = 0

    for idx in range(n * n):
        y, x = divmod(idx, n)
        if board[idx] == -1:
            # 空のマスはゴールから遠いほど良い
            score += (1 // (abs(y) + abs(x - n // 2) + 1)) * 1e-2
        else:
            # 目的の数字はゴールに近いほど良い
            score += (abs(y) + abs(x - n // 2)) * (
                1 / (abs(board[idx] - min_number) + 1) ** 4
            )

    # for i, number in enumerate(range(min_number, min(min_number + NUM_SAMPLES, n * n))):
    #     number_position = get_number_position(n, board, number)
    #     score += (abs(number_position[0]) + abs(number_position[1] - n // 2)) * (
    #         NUM_SAMPLES - i
    #     ) ** 4
    #     # score += (abs(number_position[0]) + abs(number_position[1] - n // 2)) * (
    #     #     1 / (i + 1) ** 8
    #     # )
    # # 下側に溜まった数字を減点
    # for idx in range(n // 2 * n, n * n):
    #     score += board[idx] != -1

    return score


def get_best(
    n: int,
    board: list[int],
    conveyors: list[list[tuple[int, int]]],
    min_number: int,
    depth: int = 2,
):
    if depth == 0:
        return None, evaluate(n, board, min_number)

    best_score = float("inf")
    best_operation = None

    for conveyor_idx in range(len(conveyors)):
        for steps in [-1, 1]:
            new_board = list(board)
            rotate_conveyors(conveyors, conveyor_idx, n, new_board, steps)
            _, score = get_best(n, new_board, conveyors, min_number, depth - 1)

            if score < best_score:
                best_score = score
                best_operation = (conveyor_idx, steps)

    return best_operation, best_score


def get_best_by_beam_search(
    n: int,
    board: list[int],
    conveyors: list[list[tuple[int, int]]],
    min_number: int,
    depth: int = 3,
    beam_width: int = 5,
) -> tuple[int, int]:

    current_beam = [(evaluate(n, board, min_number), list(board), None)]

    for _ in range(depth):
        next_candidates = []

        for score, current_board, first_operation in current_beam:
            for conveyor_idx, steps in itertools.product(
                range(len(conveyors)), [-1, 1]
            ):
                new_board = list(current_board)
                rotate_conveyors(conveyors, conveyor_idx, n, new_board, steps)
                new_score = evaluate(n, new_board, min_number)
                next_candidates.append(
                    (
                        new_score,
                        new_board,
                        (conveyor_idx, steps)
                        if first_operation is None
                        else first_operation,
                    )
                )

        next_candidates.sort(key=lambda x: x[0])
        current_beam = next_candidates[:beam_width]

    return current_beam[0][2]


def solve(
    n: int,
    a: list[list[int]],
) -> list[tuple[int, int]]:
    """ """

    board = list([x for row in a for x in row])
    conveyors = arrange_conveyors(n)

    operations = []

    min_number = 0
    itr = 0
    while min_number < n * n:
        if itr > 8000:
            break
        itr += 1

        if board[0 * n + n // 2] == min_number:
            board[0 * n + n // 2] = -1
            min_number += 1

        best_operation = get_best_by_beam_search(
            n, board, conveyors, min_number, depth=3, beam_width=3
        )

        operations.append(best_operation)
        rotate_conveyors(conveyors, best_operation[0], n, board, best_operation[1])

    return (conveyors, operations)


def main():
    TIME_LIMIT = 0.8
    start_time = time.perf_counter()

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
