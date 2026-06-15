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


def format_seed(
    n: int,
    seed_ids: list[int],
):
    # 1 行に空白区切りで n 個を文字列化する
    # それを改行区切りで n 行分作る
    return "\n".join(
        " ".join(map(str, seed_ids[i * n : (i + 1) * n])) for i in range(n)
    )


def main():
    n, m, t = map(int, input().split())
    total_seeds = 2 * n * (n - 1)
    x = [list(map(int, input().split())) for _ in range(total_seeds)]

    for _ in range(t):
        # 単純に、パラメーターの合計が大きい順にソートして、上位 n * n 個を残す
        seed_ids = sorted(range(total_seeds), key=lambda i: sum(x[i]), reverse=True)[
            : n * n
        ]

        # 左上から順番に、並べていく
        output_str = format_seed(n, seed_ids)

        print(output_str, flush=True)

        # 交配の結果を受け取る
        x = [list(map(int, input().split())) for _ in range(total_seeds)]


if __name__ == "__main__":
    main()
