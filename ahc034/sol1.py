"""
N x N のグリッドの高さを全て 0 にする問題
プレイヤーはダンプトラックを操作して、グリッドの高さを下げることができる
- n: グリッドの幅
- h[i][j]: グリッドの (i, j) の高さ
ダンプトラックの操作
- U, L, D, R: 上、左、下、右に移動する
- +d: 現在地から高さ d の土砂を積む
- -d: 現在地に高さ d の土砂を降ろす
"""

import sys
import random


def calc_move(
    n: int,
    prev_position: int,
    next_position: int,
):
    if prev_position - next_position == n:
        return "U"
    elif prev_position - next_position == -n:
        return "D"
    elif prev_position - next_position == 1:
        return "L"
    elif prev_position - next_position == -1:
        return "R"
    else:
        assert False, "Invalid move"


def reduce_redundant(operations: list[str]) -> list[str]:
    """
    除外項目
    - 最後の操作が U, D, L, R である場合、その移動は不要なので削除する
    - 連続する +d, -d はまとめる
    """

    reduced_operations = []


def main():
    n = int(input())
    h = []
    for _ in range(n):
        h.extend(list(map(int, input().split())))
    zero_count = sum(h[i] == 0 for i in range(n * n))

    route = []
    for i in range(n):
        route.append(i * n)
    for i in reversed(range(0, n, 2)):
        route.extend([(i + 1) * n + j for j in range(1, n)])
        route.extend([i * n + j for j in reversed(range(1, n))])
    route_length = len(route)

    # プラス：ゼロになるように土砂を積む
    # マイナス：可能ならゼロにするように降ろす
    operations = []
    current_index = 0
    current_load = 0
    remain_count = n * n - zero_count
    while remain_count > 0:
        current_posision = route[current_index]
        if h[current_posision] > 0:
            operations.append(f"+{h[current_posision]}")
            current_load += h[current_posision]
            h[current_posision] = 0
            remain_count -= 1
        elif h[current_posision] < 0:
            amount_to_unload = min(-h[current_posision], current_load)
            if amount_to_unload > 0:
                operations.append(f"-{amount_to_unload}")
                h[current_posision] += amount_to_unload
                current_load -= amount_to_unload
                if h[current_posision] == 0:
                    remain_count -= 1

        print(
            f"current_index: {current_index}, current_position: {current_posision}, h: {h[current_posision]}, current_load: {current_load}, remain_count: {remain_count}",
            file=sys.stderr,
        )
        current_index = (current_index + 1) % route_length
        operations.append(calc_move(n, current_posision, route[current_index]))

    print("\n".join(operations))


if __name__ == "__main__":
    main()
