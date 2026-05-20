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


def calc_distance(
    n: int,
    from_idx: int,
    to_idx: int,
):
    from_y, from_x = divmod(from_idx, n)
    to_y, to_x = divmod(to_idx, n)
    return abs(from_y - to_y) + abs(from_x - to_x)


def move(
    n: int,
    current_idx: int,
    target_idx: int,
) -> list[str]:
    operations = []
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

    return operations


def find_positive_max_in_row(
    n: int,
    l: list[int],
    row: int,
):
    max_value = 0
    max_idx = -1
    for i, value in enumerate(l[row * n : (row + 1) * n]):
        if value > max_value:
            max_value = value
            max_idx = i
    return -1 if max_idx == -1 else row * n + max_idx, max_value


def solve(
    n: int,
    w: list[list[int]],
    d: list[list[int]],
) -> list[str]:
    """
    重ねる操作はせず、左上から1つずつ段ボールを運び出す
    """

    operations = []

    # 高速化と副作用を避けるため、wとdは1次元配列に変換しておく
    w = [weight for row in w for weight in row]
    d = [durability for row in d for durability in row]

    # 行ごとに消化していく
    for row in range(n):
        # 行きしに一番重たい段ボールをスタックに積む
        # それを持って帰れる限り貪欲に積みながら帰る
        current_idx = 0
        while True:
            max_idx, max_value = find_positive_max_in_row(n, w, row)
            print(max_idx, divmod(max_idx, n), max_value, file=sys.stderr)
            if max_idx == -1:
                # 消化しきったとして次の行に移動
                break

            operations.extend(move(n, current_idx, max_idx))
            operations.append("1")
            w[max_idx] = -1
            current_idx = max_idx

            # 奥から順番に見て、乗せても帰れる段ボールを見つける
            for i in reversed(range(row * n, row * n + n)):
                if w[i] > 0 and w[i] * calc_distance(n, i, 0) < d[max_idx]:
                    operations.extend(move(n, current_idx, i))
                    operations.append("1")
                    current_idx = i
                    w[i] = -1
                    break

            operations.extend(move(n, current_idx, 0))
            current_idx = 0

    return operations


def main():
    n = int(input())
    w = [list(map(int, input().split())) for _ in range(n)]
    d = [list(map(int, input().split())) for _ in range(n)]

    operations = solve(n, w, d)

    print("\n".join(operations))


if __name__ == "__main__":
    main()
