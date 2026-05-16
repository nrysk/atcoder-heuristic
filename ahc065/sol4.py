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
    return (idx // n, idx % n)


def solve(
    n: int,
    a: list[list[int]],
) -> list[tuple[int, int]]:
    """
    ベルトコンベアを回転させる順番を決める。
    - 現時点で最も小さい数字の座標を取得する
    - その座標を通る横方向ベルトコンベアを x=N/2 まで回転させる
    - その座標を通る縦方向ベルトコンベアを y=0 まで回転させる
    - y=0 まで移動する途中で min_number の次の数字があれば、可能であればそちらも搬出口に移動させる
    - その座標の数字を除去する
    - これを全ての数字について繰り返す
    """

    board = [x for row in a for x in row]
    conveyors = arrange_conveyors(n)

    operations = []

    min_number = 0
    accompanied_number = 0

    while min_number < n * n:
        min_number_position = get_number_position(n, board, min_number)
        if min_number_position == (0, n // 2):
            min_number += 1
            accompanied_number = max(accompanied_number, min_number)
            continue

        # 横方向ベルトコンベアを x=N/2 まで回転させる
        conveyor_idx = min_number_position[0] // 2 + 1
        direction = (
            1
            if (min_number_position[0] % 2) ^ (min_number_position[1] < n // 2)
            else -1
        )
        operations.extend(
            rotate_conveyors(
                conveyors,
                conveyor_idx,
                n,
                board,
                direction * abs(min_number_position[1] - n // 2),
            )
        )

        # 縦方向ベルトコンベアを y=0 まで回転させる
        while True:
            min_number_position = get_number_position(n, board, min_number)
            if min_number_position[0] == 0:
                break

            if accompanied_number + 1 < n * n:
                accompanied_number_position = get_number_position(
                    n, board, accompanied_number
                )
                next_accompanied_number_position = get_number_position(
                    n, board, accompanied_number + 1
                )

            if (
                accompanied_number + 1 < n * n
                and next_accompanied_number_position[0] // 2
                > accompanied_number_position[0] // 2
            ):
                direction = (
                    1
                    if (next_accompanied_number_position[0] % 2)
                    ^ (next_accompanied_number_position[1] < n // 2)
                    else -1
                )
                # 次に同伴できる数字が現在同伴している数字よりも下のベルトコンベアにあれば、それを先に x=N/2 まで移動させる
                operations.extend(
                    rotate_conveyors(
                        conveyors,
                        next_accompanied_number_position[0] // 2 + 1,
                        n,
                        board,
                        direction * abs(next_accompanied_number_position[1] - n // 2),
                    )
                )
                accompanied_number += 1
            else:
                # 縦方向ベルトコンベアを回転させる
                conveyor_idx = 0
                direction = 1
                operations.extend(
                    rotate_conveyors(
                        conveyors,
                        conveyor_idx,
                        n,
                        board,
                        direction,
                    )
                )

        # 数字を除去する
        a[0][n // 2] = -1

        min_number += 1
        accompanied_number = max(accompanied_number, min_number)

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
