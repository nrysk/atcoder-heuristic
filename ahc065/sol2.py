"""
N x Nのグリッド上にベルトコンベアを配置し、順番に動かすことで数字を昇順に除去する問題

マスには1個の数字が配置されており、0から1N^2-1までの数字が1枚ずつ存在する。
マスにはベルトコンベアを2重まで配置できる。
ベルトコンベアは環状に配置する必要がある。
搬出口は (0, N/2) に固定されている。

制約
- N = 20
"""

import sys


def debug_board(
    board: list[list[int]],
) -> None:
    for row in board:
        print("\t".join(f"{x:2}" for x in row), flush=True, file=sys.stderr)


def arrange_conveyors(
    n: int,
) -> list[list[tuple[int, int]]]:
    """
    搬出口を通る縦向きのベルトコンベアを1つ配置する。
    縦幅2マスの横向きのベルトコンベアをN/2個配置する。
    全て時計周りを順方向とする。
    """

    conveyors = []

    # 縦向きのベルトコンベア
    conveyor = []
    conveyor.extend([(i, n // 2) for i in reversed(range(n))])
    conveyor.extend([(i, n // 2 + 1) for i in range(n)])
    conveyors.append(conveyor)

    # 横向きのベルトコンベア
    for i in range(0, n, 2):
        conveyor = []
        conveyor.extend([(i, j) for j in range(n)])
        conveyor.extend([(i + 1, j) for j in reversed(range(n))])
        conveyors.append(conveyor)

    return conveyors


def rotate_conveyors(
    conveyors: list[list[tuple[int, int]]],
    conveyor_idx: int,
    board: list[list[int]],
    direction: int,
) -> tuple[int, int]:
    """
    ベルトコンベアを回転させる。
    direction = 1: conveyor[i] -> conveyor[i+1]
    direction = -1: conveyor[i] -> conveyor[i-1]
    """

    conveyor = conveyors[conveyor_idx]
    if direction == 1:
        tmp = board[conveyor[-1][0]][conveyor[-1][1]]
        for i in reversed(range(1, len(conveyor))):
            x, y = conveyor[i]
            prev_x, prev_y = conveyor[i - 1]
            board[x][y] = board[prev_x][prev_y]
        board[conveyor[0][0]][conveyor[0][1]] = tmp
    else:
        tmp = board[conveyor[0][0]][conveyor[0][1]]
        for i in range(len(conveyor) - 1):
            x, y = conveyor[i]
            next_x, next_y = conveyor[i + 1]
            board[x][y] = board[next_x][next_y]
        board[conveyor[-1][0]][conveyor[-1][1]] = tmp

    return (conveyor_idx, direction)


def get_number_position(
    n: int,
    board: list[list[int]],
    number: int,
) -> tuple[int, int]:
    """
    数字の位置を取得する。
    """

    for x in range(n):
        for y in range(n):
            if board[x][y] == number:
                return (x, y)


def solve(
    n: int,
    a: list[list[int]],
) -> list[tuple[int, int]]:
    """
    ベルトコンベアを回転させる順番を決める。
    - 現時点で最も小さい数字の座標を取得する
    - その座標を通る横方向ベルトコンベアを x=N/2 まで回転させる
    - その座標を通る縦方向ベルトコンベアを y=0 まで回転させる
    - その座標の数字を除去する
    - これを全ての数字について繰り返す
    """

    conveyors = arrange_conveyors(n)

    operations = []

    min_number = 0
    min_number_position = get_number_position(n, a, min_number)
    if min_number_position == (0, n // 2):
        min_number += 1

    while min_number < n * n:
        # while min_number < 20:
        min_number_position = get_number_position(n, a, min_number)

        # 横方向ベルトコンベアを x=N/2 まで回転させる
        conveyor_idx = min_number_position[0] // 2 + 1
        direction = (
            1
            if (min_number_position[0] % 2) ^ (min_number_position[1] < n // 2)
            else -1
        )
        for _ in range(abs(min_number_position[1] - n // 2)):
            operations.append(rotate_conveyors(conveyors, conveyor_idx, a, direction))

        # 縦方向ベルトコンベアを y=0 まで回転させる
        conveyor_idx = 0
        direction = 1
        for _ in range(min_number_position[0]):
            operations.append(rotate_conveyors(conveyors, conveyor_idx, a, direction))

        # 数字を除去する
        a[0][n // 2] = -1

        min_number += 1

    return (conveyors, operations)


def main():
    n = int(input())
    a = [list(map(int, input().split())) for _ in range(n)]

    conveyors, operations = solve(n, a)

    # 出力
    print(len(conveyors))
    for conveyor in conveyors:
        print(len(conveyor), " ".join(f"{x} {y}" for x, y in conveyor))

    print(len(operations))
    for conveyor_idx, direction in operations:
        print(conveyor_idx, direction)


if __name__ == "__main__":
    main()
