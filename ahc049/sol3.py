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
    weights: list[int],
    durabilities: list[int],
    stack: list[int],
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

    # 移動する度に耐久力が減少することを考慮して、スタックの段ボールの耐久力を減らす
    dist = calc_distance(n, current_idx, target_idx)
    weight_sum = 0
    for idx in reversed(stack):
        durabilities[idx] -= weight_sum * dist
        weight_sum += weights[idx]

    return operations


def find_rightmost_box_in_row(n: int, board: list[int], row: int) -> int:
    for i in reversed(range(row * n, row * n + n)):
        if board[i] != -1:
            return i
    return -1


def can_return_if_loaded(
    n: int,
    weights: list[int],
    durabilities: list[int],
    current_idx: int,
    stack: list[int],
):
    """現在地点の段ボールをスタックに積んだ場合、(0, 0) に帰れるか"""
    dist = calc_distance(n, current_idx, 0)
    weight_sum = weights[current_idx]
    for idx in reversed(stack):
        if weight_sum * dist >= durabilities[idx]:
            return False
        weight_sum += weights[idx]
    return True


def solve(
    n: int,
    w: list[list[int]],
    d: list[list[int]],
) -> list[str]:
    """
    行ごとに消化していく
    一番右の段ボールを積み、帰りに貪欲に積みながら帰る
    """

    operations = []

    # 高速化と副作用を避けるため、wとdは1次元配列に変換しておく
    weights = [weight for row in w for weight in row]
    durabilities = [durability for row in d for durability in row]
    board = [i for i in range(n * n)]
    board[0] = -1  # (0, 0) は最初から空にしておく

    # 行ごとに消化していく
    for row in range(n):
        # 行きしに一番重たい段ボールをスタックに積む
        # それを持って帰れる限り貪欲に積みながら帰る
        current_idx = 0
        while True:
            stack = []
            # 一番右の段ボールを積む
            target_idx = find_rightmost_box_in_row(n, board, row)
            if target_idx == -1:
                # 消化しきったとして次の行に移動
                break
            operations.extend(
                move(n, current_idx, target_idx, weights, durabilities, stack)
            )
            operations.append("1")

            stack.append(target_idx)
            board[target_idx] = -1
            current_idx = target_idx

            for idx in reversed(range(row * n, current_idx)):
                operations.extend(
                    move(n, current_idx, idx, weights, durabilities, stack)
                )
                current_idx = idx
                if board[idx] != -1 and can_return_if_loaded(
                    n, weights, durabilities, current_idx, stack
                ):
                    operations.append("1")
                    stack.append(idx)
                    board[idx] = -1

            operations.extend(move(n, current_idx, 0, weights, durabilities, stack))
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
