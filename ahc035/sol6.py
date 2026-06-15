"""
パラメーター値の合計が最大になるように、種を交配する問題

- t: 交配の回数
- n: 畑のグリッド幅
- m: 種のパラメーター数
- x[i][j]: 種iのパラメーターjの値

交配ルール
- n x nの畑に種を植える
- 隣接するマスの種同士でランダムにパラメーターを遺伝する
- 初期の種子数は 2 * n * (n - 1) で、毎回この数だけ新しい種が生まれる
"""

import sys
from collections import deque


def format_seed(
    n: int,
    seed_ids: list[int],
):
    # 1 行に空白区切りで n 個を文字列化する
    # それを改行区切りで n 行分作る
    return "\n".join(
        " ".join(map(str, seed_ids[i * n : (i + 1) * n])) for i in range(n)
    )


def central_order(n: int) -> list[int]:
    """
    BFS を使い、中心が 0 になるような インデックス順序を生成する関数
    端に良い種が行かないように二段階で行う
    """
    order = [-1] * (n * n)
    visited = [False] * (n * n)
    queue = deque()

    # 中心のインデックスを計算
    center = (n // 2) * n + (n // 2)
    queue.append(center)
    visited[center] = True

    idx = 0
    while queue:
        current = queue.popleft()
        order[current] = idx
        idx += 1

        y, x = divmod(current, n)
        neighbors = []
        # 上、左、下、右の順で隣接マスを追加
        # 端は除外するために条件をつける
        if y > 1:
            neighbors.append((y - 1) * n + x)
        if x > 1:
            neighbors.append(y * n + (x - 1))
        if y < n - 2:
            neighbors.append((y + 1) * n + x)
        if x < n - 2:
            neighbors.append(y * n + (x + 1))

        for neighbor in neighbors:
            if not visited[neighbor]:
                visited[neighbor] = True
                queue.append(neighbor)

    # 端のマスは順番に埋めていく
    for i in range(n * n):
        if order[i] == -1:
            order[i] = idx
            idx += 1

    return order


def evaluate_seeds(
    total_seeds: int,
    m: int,
    seeds: list[list[int]],
) -> list[int]:
    """各種の評価値を計算する関数"""
    evaluations = [0] * total_seeds

    max_parameter_values = [
        max(seeds[i][j] for i in range(total_seeds)) for j in range(m)
    ]
    min_parameter_values = [
        min(seeds[i][j] for i in range(total_seeds)) for j in range(m)
    ]

    # 各パラメーターの割合を累乗することで、最大値に近いほど評価値が高くなるようにする
    for i in range(total_seeds):
        for j in range(m):
            if max_parameter_values[j] == min_parameter_values[j]:
                ratio = 1.0
            else:
                ratio = (seeds[i][j] - min_parameter_values[j]) / (
                    max_parameter_values[j] - min_parameter_values[j]
                )
            evaluations[i] += ratio**4

    return evaluations


def main():
    n, m, t = map(int, input().split())
    total_seeds = 2 * n * (n - 1)
    x = [list(map(int, input().split())) for _ in range(total_seeds)]

    order = central_order(n)

    for _ in range(t):
        # 評価値の高い順にソートして、上位 n * n 個を残す
        evaluations = evaluate_seeds(total_seeds, m, x)
        seed_ids = sorted(
            range(total_seeds), key=lambda i: evaluations[i], reverse=True
        )[: n * n]

        # 中心から外に向かって並べていく
        output_str = format_seed(n, [seed_ids[i] for i in order])

        print(output_str, flush=True)

        # 交配の結果を受け取る
        x = [list(map(int, input().split())) for _ in range(total_seeds)]


if __name__ == "__main__":
    # print(format_seed(6, central_order(6)))
    main()
