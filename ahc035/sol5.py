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


def format_seed(
    n: int,
    seed_ids: list[int],
):
    # 1 行に空白区切りで n 個を文字列化する
    # それを改行区切りで n 行分作る
    return "\n".join(
        " ".join(map(str, seed_ids[i * n : (i + 1) * n])) for i in range(n)
    )


def spiral_order(n: int) -> list[int]:
    # n x n のグリッドにおける螺旋状のインデックスを生成する関数
    order = [0] * (n * n)
    left, right, top, bottom = 0, n - 1, 0, n - 1
    idx = 0
    while left <= right and top <= bottom:
        for j in range(left, right + 1):
            order[top * n + j] = idx
            idx += 1
        top += 1

        for i in range(top, bottom + 1):
            order[i * n + right] = idx
            idx += 1
        right -= 1

        if top <= bottom:
            for j in range(right, left - 1, -1):
                order[bottom * n + j] = idx
                idx += 1
            bottom -= 1

        if left <= right:
            for i in range(bottom, top - 1, -1):
                order[i * n + left] = idx
                idx += 1
            left += 1
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
            evaluations[i] += ratio**3

    return evaluations


def main():
    n, m, t = map(int, input().split())
    total_seeds = 2 * n * (n - 1)
    x = [list(map(int, input().split())) for _ in range(total_seeds)]

    order = spiral_order(n)

    for _ in range(t):
        # 評価値の高い順にソートして、上位 n * n 個を残す
        evaluations = evaluate_seeds(total_seeds, m, x)
        print(evaluations, file=sys.stderr)
        seed_ids = sorted(
            range(total_seeds), key=lambda i: evaluations[i], reverse=True
        )[: n * n]
        seed_ids = seed_ids[::-1]

        # 螺旋状に並べていく
        output_str = format_seed(n, [seed_ids[i] for i in order])

        print(output_str, flush=True)

        # 交配の結果を受け取る
        x = [list(map(int, input().split())) for _ in range(total_seeds)]


if __name__ == "__main__":
    main()
