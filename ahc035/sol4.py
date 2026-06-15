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

import math
import random
import sys
import time


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

    # 各パラメーター値の最大値との差を減算する
    for i in range(total_seeds):
        diff_sum = 0
        for j in range(m):
            diff = max_parameter_values[j] - seeds[i][j]
            diff_sum += diff * diff
        evaluations[i] -= diff_sum

    # 各パラメーター値で1位と2位の種にはボーナスポイントを加算する
    for j in range(m):
        max_value = -1
        max_index = -1
        second_max_value = -1
        second_max_index = -1
        for i in range(total_seeds):
            if seeds[i][j] > max_value:
                second_max_value = max_value
                second_max_index = max_index
                max_value = seeds[i][j]
                max_index = i
            elif seeds[i][j] > second_max_value:
                second_max_value = seeds[i][j]
                second_max_index = i
        evaluations[max_index] += 1000000
        evaluations[second_max_index] += 10000

    return evaluations


def evaluate_field(
    n: int,
    m: int,
    seeds: list[list[int]],
    field: list[int],
    top_k_seed_ids: list[int],
) -> int:
    """
    畑全体の評価値を計算する関数
    各マスで隣接する種との、各パラメーターの最大値を算出する
    上位 K 個の種は重みを大きくして評価する
    """

    score = 0
    for y in range(n):
        for x in range(n):
            seed_id = field[y * n + x]
            weight = 10 if seed_id in top_k_seed_ids else 1

            neighbor_ids = []
            if y > 0:
                neighbor_ids.append(field[(y - 1) * n + x])
            if y < n - 1:
                neighbor_ids.append(field[(y + 1) * n + x])
            if x > 0:
                neighbor_ids.append(field[y * n + (x - 1)])
            if x < n - 1:
                neighbor_ids.append(field[y * n + (x + 1)])

            for neighbor_id in neighbor_ids:
                max_values = [0] * m
                for k in range(m):
                    max_values[k] = max(seeds[seed_id][k], seeds[neighbor_id][k])
                score += sum(max_values) * weight

    return score


def main():
    K = 8
    TIME_PER_TURN = 0.1

    n, m, t = map(int, input().split())
    total_seeds = 2 * n * (n - 1)
    seeds = [list(map(int, input().split())) for _ in range(total_seeds)]

    order = spiral_order(n)

    for _ in range(t):
        time_start = time.perf_counter()

        # 評価値の高い順にソートして、上位 n * n 個を残す
        evaluations = evaluate_seeds(total_seeds, m, seeds)
        print(evaluations, file=sys.stderr)
        seed_ids = sorted(
            range(total_seeds), key=lambda i: evaluations[i], reverse=True
        )[: n * n]
        top_k_seed_ids = seed_ids[:K]
        seed_ids = seed_ids[::-1]

        # 螺旋状に並べていく
        field = [seed_ids[i] for i in order]
        current_score = evaluate_field(n, m, seeds, field, top_k_seed_ids)

        best_score = current_score
        best_field = field[:]

        # 焼きなまし法により、畑全体の評価値を最大化するように、種の配置を改善する
        # 操作は Swap で、隣接するマスの種を入れ替える

        itr = 0
        max_temperature = 1000
        min_temperature = 1
        temperature = max_temperature
        while True:
            itr += 1
            if itr % 124 == 0:
                elapsed_time = time.perf_counter() - time_start
                if elapsed_time > TIME_PER_TURN:
                    print(
                        f"ITR: {itr}, ELAPSED: {elapsed_time:.4f} sec", file=sys.stderr
                    )
                    break

                progress = elapsed_time / TIME_PER_TURN
                temperature = (
                    max_temperature * (1 - progress) + min_temperature * progress
                )

            # 縦か横か
            if itr % 2 == 0:
                x, y = random.randint(0, n - 1), random.randint(0, n - 2)
                idx1 = x * n + y
                idx2 = x * n + (y + 1)
            else:
                x, y = random.randint(0, n - 2), random.randint(0, n - 1)
                idx1 = x * n + y
                idx2 = (x + 1) * n + y

            # Swap
            field[idx1], field[idx2] = field[idx2], field[idx1]

            next_score = evaluate_field(n, m, seeds, field, top_k_seed_ids)
            delta = next_score - current_score

            if delta > 0 or random.random() < math.exp(delta / temperature):
                current_score = next_score
                if next_score > best_score:
                    best_score = next_score
                    best_field = field[:]
            else:
                # Swap を元に戻す
                field[idx1], field[idx2] = field[idx2], field[idx1]

        output_str = format_seed(n, best_field)

        print(output_str, flush=True)

        # 交配の結果を受け取る
        seeds = [list(map(int, input().split())) for _ in range(total_seeds)]


if __name__ == "__main__":
    main()
